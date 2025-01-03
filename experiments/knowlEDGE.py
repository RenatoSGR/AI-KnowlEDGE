import streamlit as st
from ollama import chat
import PyPDF2
import docx
import datetime
import io
from typing import List, Tuple, Any
import ollama

def get_available_models_comprehension() -> List[str]:
    """Retrieves the list of names of available models with Ollama (list comprehension version)."""
    try:
        items: List[Tuple[str, Any]] = ollama.list()
        model_names: List[str] = [
            model.model
            for item in items
            if isinstance(item, tuple) and item[0] == 'models'
            for model in item[1]
        ]
        return model_names
    except Exception as e:
        print(f"Error retrieving models: {e}")
        return []

@st.cache_data
def extract_text(uploaded_file_name, uploaded_file_type, uploaded_file_bytes):
    """Extracts text from PDF, DOCX, or TXT files."""
    try:
        if uploaded_file_type == "application/pdf":
            with io.BytesIO(uploaded_file_bytes) as file_like_object:
                pdf_reader = PyPDF2.PdfReader(file_like_object)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        elif uploaded_file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(uploaded_file_bytes))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        elif uploaded_file_type == "text/plain":
            text = uploaded_file_bytes.decode('utf-8')
            return text
        else:
            st.error("Unsupported file type.")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def stream_summary_from_ollama(text, text_area_placeholder, model_name):
    """Generates a summary of the provided text and updates a text_area directly."""
    try:
        prompt = """Generate a summary of the text below.
        - If the text has a title, start with "Summary of [Title]:"
        - If no title is present, create a descriptive title and use it
        - Go straight into the summary content without any introductory phrases
        - Focus on key information and main points

        Text to summarize:
        """
        full_response = ""
        stream = chat(
            model=model_name,
            messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}],
            stream=True
        )
        update_counter = 0
        for chunk in stream:
            if 'content' in chunk['message']:
                full_response += chunk['message']['content']
                text_area_placeholder.text_area(
                    "",
                    value=full_response,
                    height=300,
                    key=f"summary_stream_{update_counter}"
                )
                update_counter += 1
        return full_response
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

@st.cache_data
def get_suggested_questions(text, model_name):
    """Generates three concise questions based on the provided text."""
    try:
        prompt = """Based on the following text, generate exactly three concise questions.
        Format each question on a new line, WITHOUT numbering or prefixes.
        Do not include any introductory text.
        Make each question standalone and thought-provoking.
        Example format:
        What is the significance of X in the text?
        How does Y contribute to the overall theme?
        Why does Z have such an impact on the outcome?

        Text to analyze:
        """
        response = chat(
            model=model_name,
            messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}]
        )
        questions = [q.strip() for q in response['message']['content'].splitlines() if q.strip()]
        return (questions + [''] * 3)[:3]
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return ["", "", ""]

def stream_answer_from_document(question, document_text, placeholder, model_name):
    """Streams an answer based on the document text."""
    try:
        full_response = ""
        messages = [{'role': 'user', 'content': f"Answer the following question based on the document: {question}\n\n{document_text}"}]
        stream = chat(
            model=model_name,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            if 'content' in chunk['message']:
                full_response += chunk['message']['content']
                placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        st.error(f"Error generating answer: {e}")
        return None

def initialize_session_state():
    """Initialize session state variables."""
    initial_states = {
        "document_text": None,
        "summary": None,
        "suggested_questions": None,
        "messages": [],
        "summary_generated": False,
        "current_file_name": None,
        "current_file_type": None,
        "current_file_bytes": None,
        "current_question": None,
        "needs_answer": False,
        "selected_model": None,
        "available_models": get_available_models_comprehension()
    }
    for key, initial_value in initial_states.items():
        if key not in st.session_state:
            st.session_state[key] = initial_value

def handle_file_upload(uploaded_file):
    """Handle file upload and state reset when a new file is uploaded."""
    if uploaded_file:
        if (uploaded_file.name != st.session_state.current_file_name or
            uploaded_file.type != st.session_state.current_file_type or
            uploaded_file.getvalue() != st.session_state.current_file_bytes):
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.current_file_type = uploaded_file.type
            st.session_state.current_file_bytes = uploaded_file.getvalue()
            document_text = extract_text(uploaded_file.name, uploaded_file.type, uploaded_file.getvalue())
            if document_text is not None:
                st.session_state.document_text = document_text
                st.session_state.summary = None
                st.session_state.summary_generated = False
                st.session_state.suggested_questions = None
                st.session_state.messages = []
                st.success("New file uploaded and processed!")

def display_text_and_summary(col1, col2):
    """Display the extracted text and summary."""
    with col1:
        with st.expander("Extracted Text", expanded=True):
            st.text_area("", st.session_state.document_text, height=300, key="extracted_text")
    with col2:
        with st.expander("Summary", expanded=True):
            if not st.session_state.summary_generated:
                text_area_placeholder = st.empty()
                with st.spinner("Generating summary..."):
                    st.session_state.summary = stream_summary_from_ollama(
                        st.session_state.document_text,
                        text_area_placeholder,
                        st.session_state.selected_model
                    )
                    st.session_state.summary_generated = True
            else:
                st.text_area(
                    "",
                    value=st.session_state.summary if st.session_state.summary else "",
                    height=300,
                    key="summary_display"
                )
            if st.session_state.summary:
                st.download_button(
                    label="Download Summary",
                    data=st.session_state.summary,
                    file_name="summary.txt",
                    mime="text/plain"
                )

def handle_suggested_question(question):
    """Handle when a suggested question is clicked."""
    st.session_state.current_question = question
    st.session_state.needs_answer = True

def display_suggested_questions():
    """Display suggested questions as clickable buttons."""
    if st.session_state.suggested_questions is None:
        with st.spinner("Generating suggested questions..."):
            st.session_state.suggested_questions = get_suggested_questions(st.session_state.document_text, st.session_state.selected_model)
    if st.session_state.suggested_questions:
        for i, question in enumerate(st.session_state.suggested_questions):
            if question and st.button(f"📝 {question}", key=f"question_button_{i}"):
                handle_suggested_question(question)

def handle_chat_interaction():
    """Process chat interactions including suggested questions and direct input."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if st.session_state.needs_answer and st.session_state.current_question:
        question = st.session_state.current_question
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "timestamp": timestamp
        })
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = stream_answer_from_document(
                question,
                st.session_state.document_text,
                placeholder,
                st.session_state.selected_model
            )
            if response:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        st.session_state.current_question = None
        st.session_state.needs_answer = False
        st.rerun()
    if prompt := st.chat_input("Ask a question about the document:"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = stream_answer_from_document(
                prompt,
                st.session_state.document_text,
                placeholder,
                st.session_state.selected_model
            )
            if response:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

def display_app_header():
    """Displays the centered app header with sparkles emojis."""
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center;">
            <h1 style='text-align: center; margin-bottom: 0;'>✨ Knowl<span style='color:#29A688'>EDGE</span> ✨</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

def app():
    """Main application function."""
    st.set_page_config(page_title="KnowlEDGE", layout="wide")

    # Ajout de ce code pour supprimer toutes les marges et padding
    st.markdown(
        """
        <style>
            /* Supprime les marges et padding de tous les éléments */
           div.stApp > div:first-child {
                padding-top: 0px !important;
            }
            div.stApp > div:first-child > div:first-child {
                padding: 0px !important;
                margin: 0px !important;
                max-width: 100% !important;
            }
            div.stApp > div:first-child > div:first-child > div:first-child {
              max-width: 100% !important;
            }
            
        </style>
        """,
        unsafe_allow_html=True,
    )

    display_app_header()
    initialize_session_state()
    if st.session_state.available_models:
        st.session_state.selected_model = st.selectbox("Select a model", st.session_state.available_models)
    else:
        st.warning("No Ollama models found. Please ensure Ollama is running and models are installed.")
    uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    handle_file_upload(uploaded_file)
    if st.session_state.document_text and st.session_state.selected_model:
        st.subheader("Document Analysis")
        col1, col2 = st.columns(2)
        display_text_and_summary(col1, col2)
        st.subheader("Suggested Questions")
        display_suggested_questions()
        st.subheader("Chat")
        handle_chat_interaction()
    elif not st.session_state.selected_model and st.session_state.available_models:
        st.info("Please select a model to proceed.")
    elif not st.session_state.available_models:
        st.error("No Ollama models found. Ensure Ollama is installed and running.")

if __name__ == "__main__":
    app()