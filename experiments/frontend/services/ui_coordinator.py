import streamlit as st

class UICoordinator:
    def __init__(self, state_manager):
        self.state_manager = state_manager

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
            self.state_manager.reset_document_states()

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