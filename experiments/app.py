import streamlit as st
from datetime import datetime
from backend import DocumentProcessor, OllamaService, Message

class KnowlEdgeApp:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ollama_service = OllamaService()

    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'processor' not in st.session_state:
            st.session_state.processor = self.document_processor
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = None
        if 'needs_answer' not in st.session_state:
            st.session_state.needs_answer = False
        if 'current_question' not in st.session_state:
            st.session_state.current_question = None
        # Track the name of the currently processed file
        if 'uploaded_file_name' not in st.session_state:
            st.session_state.uploaded_file_name = None

    def display_app_header(self):
        """Displays the centered app header with sparkles emojis."""
        st.markdown(
            """
            <div style="display: flex; justify-content: center; align-items: center;">
                <h1 style='text-align: center; margin-bottom: 0;'>✨ Knowl<span style='color:#29A688'>EDGE</span> ✨</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def handle_file_upload(self, uploaded_file):
        """Handle file upload and process the document."""
        try:
            st.session_state.processor.process_new_document(
                uploaded_file.name,
                uploaded_file.type,
                uploaded_file.getvalue()
            )
            st.success("New file uploaded and processed!")
            st.session_state.processor.summary = None
            st.session_state.processor.suggested_questions = None
            st.session_state.uploaded_file_name = uploaded_file.name  # Store the filename
        except Exception as e:
            st.error(f"Error processing file: {e}")

    def display_text_and_summary(self, col1, col2):
        """Display the extracted text and summary."""
        with col1:
            with st.expander("Extracted Text", expanded=True):
                st.text_area("", st.session_state.processor.document_text, height=300)

        with col2:
            with st.expander("Summary", expanded=True):
                if not st.session_state.processor.summary:
                    text_area_placeholder = st.empty()
                    with st.spinner("Generating summary..."):
                        summary = self.ollama_service.generate_summary(
                            st.session_state.processor.document_text,
                            st.session_state.selected_model
                        )
                        st.session_state.processor.summary = summary
                        text_area_placeholder.text_area("", value=summary, height=300)
                else:
                    st.text_area("", value=st.session_state.processor.summary, height=300)

                if st.session_state.processor.summary:
                    st.download_button(
                        label="Download Summary",
                        data=st.session_state.processor.summary,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

    def display_suggested_questions(self):
        """Display suggested questions as clickable buttons."""
        if not st.session_state.processor.suggested_questions:
            with st.spinner("Generating suggested questions..."):
                questions = self.ollama_service.generate_questions(
                    st.session_state.processor.document_text,
                    st.session_state.selected_model
                )
                st.session_state.processor.suggested_questions = questions

        for i, question in enumerate(st.session_state.processor.suggested_questions):
            if question and st.button(f"📝 {question}", key=f"question_button_{i}"):
                st.session_state.current_question = question
                st.session_state.needs_answer = True

    def handle_chat_interaction(self):
        """Process chat interactions including suggested questions and direct input."""
        for message in st.session_state.processor.messages:
            with st.chat_message(message.role):
                st.markdown(message.content)

        if st.session_state.needs_answer and st.session_state.current_question:
            self._handle_question(st.session_state.current_question)
            st.session_state.current_question = None
            st.session_state.needs_answer = False
            st.rerun()

        if prompt := st.chat_input("Ask a question about the document:"):
            self._handle_question(prompt)

    def _handle_question(self, question: str):
        timestamp = datetime.now()
        st.session_state.processor.messages.append(Message("user", question, timestamp))

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = self.ollama_service.generate_answer(
                question,
                st.session_state.processor.document_text,
                st.session_state.selected_model
            )
            placeholder.markdown(response)
            st.session_state.processor.messages.append(
                Message("assistant", response, datetime.now())
            )

    def run(self):
        """Main application function."""
        st.set_page_config(page_title="KnowlEDGE", layout="wide")

        # Remove margins and padding
        st.markdown("""
            <style>
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
        """, unsafe_allow_html=True)

        self.display_app_header()
        self.initialize_session_state()

        available_models = self.ollama_service.available_models
        if available_models:
            st.session_state.selected_model = st.selectbox("Select a model", available_models)
        else:
            st.warning("No Ollama models found. Please ensure Ollama is running and models are installed.")
            return

        uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"], key="file_uploader")

        # Process the document ONLY if a new file has been uploaded
        if uploaded_file is not None:
            if st.session_state.uploaded_file_name != uploaded_file.name:
                self.handle_file_upload(uploaded_file)

        if st.session_state.processor.document_text and st.session_state.selected_model:
            st.subheader("Document Analysis")
            col1, col2 = st.columns(2)
            self.display_text_and_summary(col1, col2)
            st.subheader("Suggested Questions")
            self.display_suggested_questions()
            st.subheader("Chat")
            self.handle_chat_interaction()
        elif not st.session_state.selected_model and available_models:
            st.info("Please select a model to proceed.")

if __name__ == "__main__":
    app = KnowlEdgeApp()
    app.run()