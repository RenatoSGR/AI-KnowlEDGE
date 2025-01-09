import streamlit as st
from aiproviders import DocumentProcessor, OllamaService
from ui.components.header import HeaderComponent
from ui.components.document_viewer import DocumentViewer
from ui.components.question_suggestions import QuestionSuggestions
from ui.components.chat_interface import ChatInterface
from ui.services.state_manager import StateManager
from ui.services.ui_coordinator import UICoordinator
from ui.styles.default_styles import STREAMLIT_STYLE

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
        
        # Initialize services
        self.state_manager = StateManager(self.document_processor, self.ollama_service)
        self.ui_coordinator = UICoordinator(self.state_manager)
        
        # Initialize UI components
        self.document_viewer = DocumentViewer(self.ollama_service)
        self.question_suggestions = QuestionSuggestions(self.ollama_service)
        self.chat_interface = ChatInterface(self.ollama_service)

    def run(self):
        """
        Main application entry point. Sets up the interface and manages the application flow.
        """
        st.set_page_config(page_title="AI KnowlEDGE", layout="wide")

        # Apply custom styling
        st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

        # Display header and initialize session state
        HeaderComponent.render()
        self.state_manager.initialize_session_state()

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
            "Upload a pdf, docx, or txt file",
            type=["pdf", "docx", "txt"],
            key="file_uploader"
        )

        if uploaded_file is not None:
            self.ui_coordinator.handle_file_upload(uploaded_file)

        # Display content if document is loaded
        if st.session_state.processor.document_text and st.session_state.selected_model:
            st.subheader("Document Analysis")
            col1, col2 = st.columns(2)
            self.document_viewer.display_text_and_summary(col1, col2)

            if st.session_state.processor.summary and not st.session_state.summary_in_progress:
                st.subheader("Suggested Questions")
                self.question_suggestions.display_suggested_questions()

            st.subheader("Chat")
            self.chat_interface.handle_chat_interaction()
        elif not st.session_state.selected_model and available_models:
            st.info("Please select a model to proceed.")

if __name__ == "__main__":
    app = KnowlEdgeApp()
    app.run()