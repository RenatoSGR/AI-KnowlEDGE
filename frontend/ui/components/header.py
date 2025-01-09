import streamlit as st

class HeaderComponent:
    @staticmethod
    def render():
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