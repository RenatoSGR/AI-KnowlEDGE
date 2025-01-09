from typing import Optional, List
import io
import PyPDF2
import docx
from datetime import datetime
from .message import Message
from .vector_store import VectorStore
from .config import NUM_CHUNKS_TO_RETRIEVE
import requests

class DocumentProcessor:
    def __init__(self):
        # Keep all your existing initializations
        self.document_text: Optional[str] = None
        self.summary: Optional[str] = None
        self.suggested_questions: Optional[List[str]] = None
        self.messages: List[Message] = []
        self.token_count: Optional[int] = None
        
        # Add vector store for RAG
        self.vector_store = VectorStore()
    
    def extract_text(self, file_name: str, file_type: str, file_bytes: bytes) -> Optional[str]:
        # Your existing extract_text implementation - unchanged
        try:
            if file_type == "application/pdf":
                with io.BytesIO(file_bytes) as file_like_object:
                    pdf_reader = PyPDF2.PdfReader(file_like_object)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(io.BytesIO(file_bytes))
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            elif file_type == "text/plain":
                return file_bytes.decode('utf-8')
            else:
                raise ValueError("Unsupported file type")
        except Exception as e:
            raise Exception(f"Error extracting text: {e}")
        

    def extract_text_ocr(self, file_name: str, file_type: str, file_bytes: bytes) -> Optional[str]:
        files = {'file': file_bytes}  
        response = requests.post("http://localhost:8000/analyze/", files=files)
        if response.status_code == 200:  
            response = response.json()["text"]
            return response


    def process_new_document(self, file_name: str, file_type: str, file_bytes: bytes) -> None:
        # Extract text and reset states as before
        self.document_text = self.extract_text_ocr(file_name, file_type, file_bytes)
        self.summary = None
        self.suggested_questions = None
        self.messages = []
        self.token_count = None
        
        # Add document to vector store if text was extracted successfully
        if self.document_text:
            # Clear previous document's embeddings
            self.vector_store.clear()
            
            # Add new document with metadata
            self.vector_store.add_document(
                self.document_text,
                metadata={
                    'source': file_name,
                    'type': file_type,
                    'timestamp': datetime.now().isoformat()
                }
            )

    def get_relevant_chunks(self, query: str, k: int = NUM_CHUNKS_TO_RETRIEVE) -> List[str]:
        """
        Get relevant document chunks for a query.
        This is a new method to support RAG-based question answering.
        """
        if not self.document_text:
            raise ValueError("No document has been processed yet")
            
        return self.vector_store.get_relevant_chunks(query, k)

    def cleanup(self):
        """Clean up resources when shutting down the application"""
        if hasattr(self, 'vector_store'):
            self.vector_store.clear()

    def health_check(self) -> bool:
        """Check if all components are healthy and operational"""
        if not self.vector_store:
            return False
        return self.vector_store.health_check()