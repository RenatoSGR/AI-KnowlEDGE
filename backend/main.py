import streamlit as st
import time


def reset_session_state():
    st.session_state.conversation = None
    st.session_state.chat_history = None
    st.session_state.messages = []
    st.session_state.uploaded_files = []


def initialize_docker(yml_path):
    start_docker_compose(yml_path)
    return get_endpoint_from_docker_compose(yml_path)


def get_azure_key(env_path):
    return get_key(env_path)


def analyze_uploaded_document(client, document_file):
    start = time.time()
    result = analyze_document(client, document_file)
    elapsed = time.time() - start
    return get_results(result), elapsed


def main():
    st.title("Doc KnowlEDGE")
    st.sidebar.header('Upload Menu')

    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = []

    uploaded_files = st.sidebar.file_uploader(
        'Upload files', type=['pdf', 'txt', 'docx'], 
        accept_multiple_files=True
    )

    if uploaded_files:
        st.session_state['uploaded_files'].extend(uploaded_files)

    st.sidebar.header('Uploaded Files')

    for uploaded_file in st.session_state['uploaded_files']:
        st.sidebar.write(uploaded_file.name)

    if st.sidebar.button('Reset'):
        reset_session_state()

    if st.sidebar.button('Analyze'):
        if st.session_state['uploaded_files']:
            yml_path = "docker-compose.yml"
            azure_env_path = "azure.env"

            #endpoint = initialize_docker(yml_path)
            #key = get_azure_key(azure_env_path)
            client = get_document_intelligence_client(
                "http://localhost:5000", 
                "<YOUR_AZURE>"
            )

            for uploaded_file in st.session_state['uploaded_files']:
                document_info, elapsed_time = analyze_uploaded_document(client, "example.png")
                st.write(f"Document: {uploaded_file.name}")
                st.write(f"Analysis Time: {elapsed_time:.2f} seconds")
                st.write(document_info)

if __name__ == "__main__":
    main()