import streamlit as st

class HeaderComponent:
    @staticmethod
    def render():
        """
        Affiche l'en-tête de l'application avec un style personnalisé.
        Crée un en-tête centré avec du texte à code couleur, des emojis d'étincelles et un sous-titre cursif.
        """
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center;">
                <h1 style='text-align: center; margin-bottom: 0px;'>
                    ✨ <span style='color:#3B82F6'>AI</span> knowl<span style='color:#29A688'>EDGE</span> ✨
                </h1>
                <h2 style='font-family: "Brush Script MT", cursive; font-weight: normal; font-size: 2.1em; margin-top: -22px;'>
                    Your <span style='color:#29A688'>Disconnected</span> Documents <span style='color:#3B82F6'>Analyzer</span>
                </h2>
            </div>
            """,
            unsafe_allow_html=True,
        )