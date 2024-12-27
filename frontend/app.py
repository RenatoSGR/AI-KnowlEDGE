import requests
import streamlit as st

def reset_conversation():
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.messages = []


def reset_session_state():
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.messages = []
    st.session_state.uploaded_files = []


def display_title():
    st.title("Doc KnowlEDGE Chat")
    st.sidebar.header('Upload Menu')


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = []


def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)


def upload_files():
    uploaded_files = st.sidebar.file_uploader(
        'Upload files', type=['pdf', 'txt', 'docx'], 
        accept_multiple_files=True,
        key='file_uploader'
    )
    if uploaded_files:
        st.session_state['uploaded_files'].extend(uploaded_files)


def analyze_files():
    if st.session_state['uploaded_files']:
        for idx, uploaded_file in enumerate(st.session_state['uploaded_files']):
            files = {'file': uploaded_file.getvalue()}  
            response = requests.post("http://localhost:8000/analyze/", files=files)  
            if response.status_code == 200:  
                st.write(f"Document: {uploaded_file.name}", key=f'document_{idx}')
                st.write(response.json()["text"], key=f'text_{idx}')
                return True


def handle_user_input():
    if question := st.chat_input("Ask me anything about your document"):
        st.chat_message("user").markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})

        response = requests.post("http://localhost:8000/chat/", json={"question": question})

        if response.status_code == 200:  
            with st.chat_message("assistant"):
                reply = response.json().get("response")
                st.markdown(reply, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply})


def main():
    display_title()
    initialize_session_state()
    upload_files()
    if analyze_files():
        display_chat_history()
        handle_user_input()

if __name__ == "__main__":
    main()