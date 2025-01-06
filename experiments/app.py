import streamlit as st
from datetime import datetime
from backend import DocumentProcessor, OllamaService, Message
from pathlib import Path

class KnowlEdgeApp:
    """
    Main application class that handles the document analysis interface.
    This class coordinates the document processing, RAG-based question answering,
    and Streamlit interface components.
    """

    def __init__(self):
        """Initialize core components of the application."""
        self.document_processor = DocumentProcessor()
        self.ollama_service = OllamaService()

    def initialize_session_state(self):
        """
        Initialize session state variables for maintaining state across Streamlit reruns.
        Sets up all necessary variables with their default values if they don't exist.
        """
        initial_states = {
            'processor': self.document_processor,
            'selected_model': None,
            'needs_answer': False,
            'current_question': None,
            'uploaded_file_name': None,
            'summary_in_progress': False,
            'questions_generated': False,
            'update_counter': 0,
            'display_chunks': False,
            'chat_history_with_context': [], # Add a list to store chat history with context
            'extracting_text': False  # Flag for text extraction status
        }

        for key, initial_value in initial_states.items():
            if key not in st.session_state:
                st.session_state[key] = initial_value

    def display_app_header(self):
        """
        Display the application header with custom styling.
        Creates a centered header with color-coded text and sparkle emojis.
        """
        st.markdown(
            """
            <div style="display: flex; justify-content: center; align-items: center;">
                <h1 style='text-align: center; margin-bottom: 0;'>
                    ✨ <span style='color:#3B82F6'>AI</span> knowl<span style='color:#29A688'>EDGE</span> ✨
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def display_text_and_summary(self, col1, col2):
        """
        Display the document text and generate/display its summary.
        Shows the original text in one column and its summary in another,
        handling token estimation and summary generation.
        """
        with col1:
            if st.session_state.processor.token_count is None and st.session_state.processor.document_text:
                estimated_tokens = self.ollama_service._estimate_tokens(
                    st.session_state.processor.document_text
                )
                st.session_state.processor.token_count = estimated_tokens

            with st.expander("Extracted Text" + (
                f" (Estimated tokens: {st.session_state.processor.token_count:,})"
                if st.session_state.processor.token_count is not None else ""
            ), expanded=True):
                if st.session_state.extracting_text:
                    st.info("Extracting text from document...")
                else:
                    st.text_area(
                        "",
                        st.session_state.processor.document_text,
                        height=300,
                        key="extracted_text"
                    )

        with col2:
            with st.expander("Summary", expanded=True):
                if not st.session_state.processor.summary and not st.session_state.summary_in_progress:
                    text_area_placeholder = st.empty()
                    with st.spinner("Generating summary..."):
                        st.session_state.summary_in_progress = True
                        full_response = ""

                        try:
                            for response in self.ollama_service.generate_summary(
                                st.session_state.processor.document_text,
                                st.session_state.selected_model
                            ):
                                if response.is_error:
                                    st.error(response.error_message)
                                    break

                                full_response += response.content
                                text_area_placeholder.text_area(
                                    "",
                                    value=full_response,
                                    height=300,
                                    key=f"summary_stream_{st.session_state.update_counter}"
                                )
                                st.session_state.update_counter += 1

                            if not response.is_error:
                                st.session_state.processor.summary = full_response
                        finally:
                            st.session_state.summary_in_progress = False
                else:
                    st.text_area(
                        "",
                        value=st.session_state.processor.summary or "",
                        height=300,
                        key="summary_display"
                    )

                if st.session_state.processor.summary:
                    if st.button("Regenerate Summary"):
                        st.session_state.processor.summary = None
                        st.session_state.summary_in_progress = False
                        st.rerun()
                    st.download_button(
                        label="Download Summary",
                        data=st.session_state.processor.summary,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

    def display_suggested_questions(self):
        """
        Generate and display suggested questions about the document.
        """
        if not st.session_state.questions_generated:
            if not st.session_state.processor.suggested_questions and not st.session_state.summary_in_progress:
                with st.spinner("Generating suggested questions..."):
                    try:
                        questions = self.ollama_service.generate_questions(
                            st.session_state.processor.document_text,
                            st.session_state.selected_model,
                            summary=st.session_state.processor.summary
                        )
                        st.session_state.processor.suggested_questions = questions
                        st.session_state.questions_generated = True
                    except Exception as e:
                        st.error(f"Error generating questions: {e}")
                        return

        # Display logic
        if st.session_state.questions_generated and st.session_state.processor.suggested_questions:
            for i, question in enumerate(st.session_state.processor.suggested_questions):
                if question and st.button(f"📝 {question}", key=f"question_button_{i}"):
                    st.session_state.current_question = question
                    st.session_state.needs_answer = True
                    st.session_state.display_chunks = True
                    st.rerun()
        elif st.session_state.questions_generated and not st.session_state.processor.suggested_questions:
            st.info("No suggested questions were generated.")
        elif not st.session_state.questions_generated and not st.session_state.summary_in_progress:
            st.info("Generating suggested questions...")
        elif st.session_state.summary_in_progress:
            st.info("Please wait for the summary to be generated before generating questions.")

    def _handle_question(self, question: str):
        """
        Handle individual questions using RAG-enhanced answer generation.
        """
        timestamp = datetime.now()
        st.session_state.processor.messages.append(Message("user", question, timestamp))
        st.session_state.chat_history_with_context.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            relevant_chunks_for_display = []

            with st.spinner("Generating answer..."):
                try:
                    # Retrieve relevant context chunks using RAG
                    relevant_chunks = st.session_state.processor.get_relevant_chunks(
                        question,
                        k=3
                    )
                    relevant_chunks_for_display = list(relevant_chunks)

                    # Generate answer using the retrieved context
                    for response in self.ollama_service.generate_answer(
                        question,
                        relevant_chunks,
                        st.session_state.selected_model
                    ):
                        if response.is_error:
                            st.error(response.error_message)
                            break

                        full_response += response.content
                        placeholder.markdown(full_response)  # Update the placeholder as text is generated
                        break # Stop the spinner as soon as we get the first response

                    if not response.is_error:
                        st.session_state.chat_history_with_context.append(
                            {"role": "assistant", "content": full_response, "context": relevant_chunks_for_display}
                        )

                        if relevant_chunks_for_display:
                            with st.expander("View source context"):
                                for i, chunk in enumerate(relevant_chunks_for_display, 1):
                                    st.markdown(f"**Context {i}:**")
                                    st.markdown(chunk)
                                    st.markdown("---")

                        st.session_state.processor.messages.append(
                            Message("assistant", full_response, datetime.now())
                        )

                except Exception as e:
                    st.error(f"Error generating answer: {e}")

            # Continue streaming the answer after the spinner is gone
            if full_response:
                for response in self.ollama_service.generate_answer(
                    question,
                    relevant_chunks,
                    st.session_state.selected_model
                ):
                    if response.is_error:
                        st.error(response.error_message)
                        break
                    if not response.content in full_response: # Avoid re-printing the first part
                        full_response += response.content
                        placeholder.markdown(full_response)

    def handle_chat_interaction(self):
        """
        Process chat interactions including suggested questions and direct input.
        Manages the chat interface, message history, and question handling.
        """
        # Display existing messages with context
        for item in st.session_state.chat_history_with_context:
            with st.chat_message(item["role"]):
                st.markdown(item["content"])
                if item["role"] == "assistant" and "context" in item and item["context"]:
                    if not st.session_state.current_question or item["content"] != st.session_state.chat_history_with_context[-1]["content"]:
                        with st.expander("View source context"):
                            for i, chunk in enumerate(item["context"], 1):
                                st.markdown(f"**Context {i}:**")
                                st.markdown(chunk)
                                st.markdown("---")

        # Handle pending questions
        if st.session_state.needs_answer and st.session_state.current_question:
            self._handle_question(st.session_state.current_question)
            st.session_state.current_question = None
            st.session_state.needs_answer = False

        # Handle new questions
        if prompt := st.chat_input("Ask a question about the document:"):
            self._handle_question(prompt)

    def process_new_document(self, file_name: str, file_type: str, file_bytes: bytes):
        """
        Process a new document and reset relevant application state.
        Handles document processing and initializes RAG components.
        """
        st.session_state.extracting_text = True
        try:
            with st.spinner("Extracting text from document..."):
                st.session_state.processor.process_new_document(file_name, file_type, file_bytes)
                st.session_state.uploaded_file_name = file_name
                st.success("New file uploaded and processed!")

            # Reset states for new document
            st.session_state.update_counter = 0
            st.session_state.summary_in_progress = False
            st.session_state.questions_generated = False
            st.session_state.processor.suggested_questions = None
            st.session_state.chat_history_with_context = [] # Clear chat history

        except Exception as e:
            st.error(f"Error processing file: {e}")
        finally:
            st.session_state.extracting_text = False

    def handle_file_upload(self, uploaded_file):
        """Handle file upload and document processing."""
        if uploaded_file.name != st.session_state.uploaded_file_name:
            self.process_new_document(
                uploaded_file.name,
                uploaded_file.type,
                uploaded_file.getvalue()
            )

    def run(self):
        """
        Main application entry point. Sets up the interface and manages the application flow.
        """
        st.set_page_config(page_title="AI KnowlEDGE", layout="wide")

        # Remove margins and padding for better layout
        st.markdown(
            """
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
            """,
            unsafe_allow_html=True
        )

        self.display_app_header()
        self.initialize_session_state()

        # Model selection
        available_models = self.ollama_service.available_models
        if available_models:
            st.session_state.selected_model = st.selectbox(
                "Select a model",
                available_models,
                key="model_selector"
            )
        else:
            st.warning("No Ollama models found. Please ensure Ollama is running and models are installed.")
            return

        # File upload
        uploaded_file = st.file_uploader(
            "Upload a PDF, DOCX, or TXT file",
            type=["pdf", "docx", "txt"],
            key="file_uploader"
        )

        if uploaded_file is not None:
            self.handle_file_upload(uploaded_file)

        # Display content if document is loaded
        if st.session_state.processor.document_text and st.session_state.selected_model:
            st.subheader("Document Analysis")
            col1, col2 = st.columns(2)
            self.display_text_and_summary(col1, col2)

            if st.session_state.processor.summary and not st.session_state.summary_in_progress:
                st.subheader("Suggested Questions")
                self.display_suggested_questions()

            st.subheader("Chat")
            self.handle_chat_interaction()
        elif not st.session_state.selected_model and available_models:
            st.info("Please select a model to proceed.")

if __name__ == "__main__":
    app = KnowlEdgeApp()
    app.run()