import streamlit as st
from backend import DocumentProcessor, OllamaService

class StateManager:
    def __init__(self, document_processor: DocumentProcessor, ollama_service: OllamaService):
        self.document_processor = document_processor
        self.ollama_service = ollama_service

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
            'chat_history_with_context': [],
            'extracting_text': False
        }

        for key, initial_value in initial_states.items():
            if key not in st.session_state:
                st.session_state[key] = initial_value

    def reset_document_states(self):
        """Reset states for new document processing"""
        st.session_state.update_counter = 0
        st.session_state.summary_in_progress = False
        st.session_state.questions_generated = False
        st.session_state.processor.suggested_questions = None
        st.session_state.chat_history_with_context = []