import streamlit as st
from ollama import chat
import PyPDF2
import docx
import datetime

def extract_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text

        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text

        elif uploaded_file.type == "text/plain":
            text = uploaded_file.read().decode('utf-8')
            return text

        else:
            st.error("Unsupported file type.")
            return None

    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF: {e}")
        return None
    except UnicodeDecodeError:
        st.error("Error decoding the text file. Please ensure it's UTF-8 encoded.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def stream_summary_from_ollama(text, summary_container):
    try:
        prompt = """Generate a summary of the text below. 
        - If the text has a title, start with "Summary of [Title]:"
        - If no title is present, create a descriptive title and use it
        - Go straight into the summary content without any introductory phrases like "Here is a summary" or "This text"
        - Focus on key information and main points
        
        Text to summarize:
        """
        
        full_response = ""
        with summary_container:
            stream = chat(
                model="phi3.5",
                messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}],
                stream=True
            )
            summary_display = st.empty()
            counter = 0
            for chunk in stream:
                if 'content' in chunk['message']:
                    full_response += chunk['message']['content']
                    counter += 1
                    summary_display.text_area(
                        "Summary (Generating...)", 
                        full_response, 
                        height=300, 
                        key=f"summary_streaming_{counter}"
                    )
            # Update final display without "Generating..." text
            summary_display.text_area(
                "Summary", 
                full_response, 
                height=300, 
                key="summary_final"
            )
        return full_response
    except Exception as e:
        st.error(f"Error streaming summary from Ollama: {e}")
        return None

def stream_answer_from_document(question, document_text, placeholder):
    try:
        full_response = ""
        stream = chat(
            model="phi3.5",
            messages=[{'role': 'user', 'content': f"Answer the following question based on the document: {question} \n\n{document_text}"}],
            stream=True
        )
        for chunk in stream:
            if 'content' in chunk['message']:
                full_response += chunk['message']['content']
                placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        st.error(f"Error streaming answer from Ollama: {e}")
        return None

def get_suggested_questions(text):
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
            model="llama3.2",
            messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}]
        )
        # Split by newline and clean up empty lines
        questions = [q.strip() for q in response['message']['content'].splitlines() if q.strip()]
        # Take exactly three questions, pad with empty strings if less than 3
        questions = (questions + [''] * 3)[:3]
        return questions
    except Exception as e:
        st.error(f"Error calling Ollama for question generation: {e}")
        return None

def initialize_session_state():
    """Initialize all session state variables if they don't exist."""
    initial_states = {
        "document_text": None,
        "summary": None,
        "suggested_questions": None,
        "messages": [],
        "summary_generated": False,
        "current_file": None
    }
    for key, initial_value in initial_states.items():
        if key not in st.session_state:
            st.session_state[key] = initial_value

def handle_file_upload(uploaded_file):
    """Handle file upload and state reset when a new file is uploaded."""
    if uploaded_file and uploaded_file != st.session_state.current_file:
        st.session_state.current_file = uploaded_file
        document_text = extract_text(uploaded_file)
        if document_text is not None:
            st.session_state.document_text = document_text
            st.session_state.summary = None
            st.session_state.summary_generated = False
            st.session_state.suggested_questions = None
            st.session_state.messages = []

def display_text_and_summary(col1, col2):
    """Display the extracted text and generate/display summary."""
    with col1:
        st.text_area("Extracted Text", st.session_state.document_text, height=300, key="extracted_text")

    with col2:
        if not st.session_state.summary_generated:
            with st.spinner("Initializing summary generation..."):
                st.session_state.summary = stream_summary_from_ollama(st.session_state.document_text, col2)
                st.session_state.summary_generated = True
        else:
            st.text_area("Summary", st.session_state.summary, height=300, key="summary_display")

def display_suggested_questions():
    """Generate and display suggested questions."""
    if st.session_state.suggested_questions is None:
        with st.spinner("Generating suggested questions..."):
            st.session_state.suggested_questions = get_suggested_questions(st.session_state.document_text)

    if st.session_state.suggested_questions:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Question 1:** {st.session_state.suggested_questions[0]}")
        with col2:
            st.markdown(f"**Question 2:** {st.session_state.suggested_questions[1]}")
        with col3:
            st.markdown(f"**Question 3:** {st.session_state.suggested_questions[2]}")
    else:
        st.error("Could not generate questions.")

def handle_chat_interaction():
    """Handle chat messages display and new question processing."""
    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new questions
    if prompt := st.chat_input("Ask a question about the document or its summary:"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt, 
            "timestamp": timestamp
        })
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process and display assistant response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response_text = stream_answer_from_document(
                prompt, 
                st.session_state.summary or st.session_state.document_text, 
                placeholder
            )
            if response_text:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text, 
                    "timestamp": timestamp
                })

def app():
    """Main application function orchestrating the UI components."""
    st.set_page_config(page_title="KnowlEDGE", layout="wide")
    st.title("KnowlEDGE")

    # Initialize session state
    initialize_session_state()

    # File upload section
    uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    handle_file_upload(uploaded_file)

    # Main content section
    if st.session_state.document_text:
        st.subheader("Extracted Text and Summary")
        col1, col2 = st.columns(2)
        display_text_and_summary(col1, col2)

        st.subheader("Suggested Questions")
        display_suggested_questions()

        st.subheader("Ask a Question")
        handle_chat_interaction()

if __name__ == "__main__":
    app()