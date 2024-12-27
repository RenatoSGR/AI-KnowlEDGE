import streamlit as st

def reset_conversation():
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.messages = []
    st.session_state.uploaded_files = []


def call_openai_rag(prompt):
    return "You said: " + prompt, []

st.title("Doc KnowlEDGE")
st.sidebar.header('Upload Menu')

if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []

uploaded_files = st.sidebar.file_uploader('Upload files', type=['pdf', 'txt', 'docx'], accept_multiple_files=True)

if uploaded_files:
    st.session_state['uploaded_files'].extend(uploaded_files)

st.sidebar.header('Uploaded Files')
for uploaded_file in st.session_state['uploaded_files']:
    st.sidebar.write(uploaded_file.name)

st.header('Chat')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("What is up?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    response, citations = call_openai_rag(prompt=prompt)

    with st.chat_message("assistant"):
        st.markdown(response, unsafe_allow_html=True)
        for citation in citations:
            create_unclickable_link(citation)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.button("Clear History", on_click=reset_conversation)