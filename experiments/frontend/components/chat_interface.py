import streamlit as st
from datetime import datetime
from backend import Message, OllamaService

class ChatInterface:
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service

    def _handle_question(self, question: str):
        """
        Handle individual questions using RAG-enhanced answer generation.
        """
        timestamp = datetime.now()
        st.session_state.processor.messages.append(Message("user", question, timestamp))

        # Add user message to chat history first
        st.session_state.chat_history_with_context.append({"role": "user", "content": question})

        # Pre-insert an assistant entry with empty content, indicators for context loading and display
        st.session_state.chat_history_with_context.append({
            "role": "assistant",
            "content": "",
            "context": [],
            "context_loaded": False,
            "context_displayed": False
        })

        with st.chat_message("user"):
            st.markdown(question)

        # Use a placeholder for the entire assistant message
        assistant_placeholder = st.empty()

        relevant_chunks_for_display = []
        with assistant_placeholder.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            with st.spinner("Generating answer..."):
                try:
                    # Retrieve relevant chunks only if they haven't been loaded yet
                    if not st.session_state.chat_history_with_context[-1]["context_loaded"]:
                        relevant_chunks = st.session_state.processor.get_relevant_chunks(question, k=3)
                        relevant_chunks_for_display = list(relevant_chunks)

                        # Update the assistant entry with context and set the flag to True
                        st.session_state.chat_history_with_context[-1]["context"] = relevant_chunks_for_display
                        st.session_state.chat_history_with_context[-1]["context_loaded"] = True

                    for response in self.ollama_service.generate_answer(
                        question,
                        relevant_chunks_for_display,
                        st.session_state.selected_model
                    ):
                        if response.is_error:
                            st.error(response.error_message)
                            break
                        full_response += response.content
                        placeholder.markdown(full_response)

                        # Update the assistant entry's content as we stream
                        st.session_state.chat_history_with_context[-1]["content"] = full_response

                    st.session_state.processor.messages.append(
                        Message("assistant", full_response, datetime.now())
                    )

                except Exception as e:
                    st.error(f"Error generating answer: {e}")

            # Correctly set context_displayed to True only after expander is rendered
            if relevant_chunks_for_display:
                with st.expander("View source context"):
                    for i, chunk in enumerate(relevant_chunks_for_display, 1):
                        st.markdown(f"**Context {i}:**")
                        st.markdown(chunk)
                        st.markdown("---")
                    # Set context_displayed to True after rendering the expander
                    st.session_state.chat_history_with_context[-1]["context_displayed"] = True

    def handle_chat_interaction(self):
        """
        Process chat interactions including suggested questions and direct input.
        Manages the chat interface, message history, and question handling.
        """
        # Create a container for the chat history
        chat_history_container = st.container()

        with chat_history_container:
            for item in st.session_state.chat_history_with_context:
                if item["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(item["content"])
                elif item["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(item["content"])
                        if item.get("context") and item.get("context_displayed"):
                            with st.expander("View source context", expanded=False):
                                for i, chunk in enumerate(item["context"], 1):
                                    st.markdown(f"**Context {i}:**")
                                    st.markdown(chunk)
                                    st.markdown("---")

        # Handle new question or input
        if st.session_state.needs_answer and st.session_state.current_question:
            self._handle_question(st.session_state.current_question)
            st.session_state.current_question = None
            st.session_state.needs_answer = False

        if prompt := st.chat_input("Ask a question about the document:"):
            self._handle_question(prompt)