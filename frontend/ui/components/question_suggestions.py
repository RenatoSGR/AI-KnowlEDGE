import streamlit as st
from aiproviders import OllamaService

class QuestionSuggestions:
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service

    def display_suggested_questions(self):
        """
        Generate and display suggested questions about the document.
        """
        if not st.session_state.questions_generated:
            if not st.session_state.processor.suggested_questions and not st.session_state.summary_in_progress:
                with st.spinner("Generating suggested questions..."):
                    try:
                        questions = self.ollama_service.generate_questions(
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