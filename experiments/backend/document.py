from typing import Optional, List
import io
import PyPDF2
import docx
from .message import Message

class DocumentProcessor:
    def __init__(self):
        self.document_text: Optional[str] = None
        self.summary: Optional[str] = None
        self.suggested_questions: Optional[List[str]] = None
        self.messages: List[Message] = []
        self.token_count: Optional[int] = None  
        
    def extract_text(self, file_name: str, file_type: str, file_bytes: bytes) -> Optional[str]:
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

    def process_new_document(self, file_name: str, file_type: str, file_bytes: bytes) -> None:
        self.document_text = self.extract_text(file_name, file_type, file_bytes)
        self.summary = None
        self.suggested_questions = None
        self.messages = []
        self.token_count = None  # Reset token count for new document