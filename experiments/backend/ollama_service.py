from typing import List, Any, Tuple, Optional, Generator
from dataclasses import dataclass
import ollama
from ollama import chat
import textwrap

@dataclass
class StreamResponse:
    content: str
    is_error: bool = False
    error_message: Optional[str] = None

class OllamaService:
    def __init__(self):
        self._available_models: Optional[List[str]] = None

    @property
    def available_models(self) -> List[str]:
        if self._available_models is None:
            self._available_models = self._get_available_models()
        return self._available_models

    def _get_available_models(self) -> List[str]:
        try:
            items: List[Tuple[str, Any]] = ollama.list()
            return [
                model.model
                for item in items
                if isinstance(item, tuple) and item[0] == 'models'
                for model in item[1]
            ]
        except Exception as e:
            print(f"Error retrieving models: {e}")
            return []

    def _split_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into chunks of approximately equal size."""
        # First split by double newlines to preserve paragraph structure
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            # If a single paragraph is too long, split it further
            if len(paragraph) > chunk_size:
                # Split into sentences (roughly)
                sentences = paragraph.replace('. ', '.\n').split('\n')
                for sentence in sentences:
                    if current_size + len(sentence) > chunk_size and current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                    current_chunk.append(sentence)
                    current_size += len(sentence)
            else:
                if current_size + len(paragraph) > chunk_size and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                current_chunk.append(paragraph)
                current_size += len(paragraph)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def generate_summary(self, text: str, model_name: str) -> Generator[StreamResponse, None, None]:
        """
        Generates a summary using a custom map-reduce approach.
        """
        try:
            # Split text into chunks
            chunks = self._split_text(text)
            
            # Map phase: Summarize each chunk
            chunk_summaries = []
            map_prompt = """Summarize the following text extract. Focus on key information and main points:

            {text}

            Summary:"""
            
            for chunk in chunks:
                response = ollama.chat(
                    model=model_name,
                    messages=[{
                        'role': 'user',
                        'content': map_prompt.format(text=chunk)
                    }]
                )
                chunk_summaries.append(response['message']['content'])
            
            # Reduce phase: Combine summaries
            combined_text = "\n\n".join(chunk_summaries)
            reduce_prompt = """Combine these summaries into a single coherent summary. 
            Maintain a clear narrative flow and eliminate redundancy:

            {text}

            Final Summary:"""
            
            stream = ollama.chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': reduce_prompt.format(text=combined_text)
                }],
                stream=True
            )
            
            for chunk in stream:
                if 'content' in chunk['message']:
                    yield StreamResponse(content=chunk['message']['content'])

        except Exception as e:
            yield StreamResponse(
                content="",
                is_error=True,
                error_message=f"Error generating summary: {str(e)}"
            )

    def generate_questions(self, text: str, model_name: str) -> List[str]:
        try:
            messages = [{'role': 'user', 'content': f"""Based on the following text, generate exactly three concise questions.
            Format each question on a new line, WITHOUT numbering or prefixes.
            Do not include any introductory text.
            Make each question standalone and thought-provoking.

            Text to analyze: {text}"""}]
            
            response = chat(model=model_name, messages=messages)
            questions = [q.strip() for q in response['message']['content'].splitlines() if q.strip()]
            return (questions + [''] * 3)[:3]
        except Exception as e:
            raise Exception(f"Error generating questions: {e}")

    def generate_answer(self, question: str, document_text: str, model_name: str) -> Generator[StreamResponse, None, None]:
        try:
            messages = [{'role': 'user', 'content': f"Answer the following question based on the document: {question}\n\n{document_text}"}]
            stream = chat(model=model_name, messages=messages, stream=True)
            
            for chunk in stream:
                if 'content' in chunk['message']:
                    yield StreamResponse(content=chunk['message']['content'])
        except Exception as e:
            yield StreamResponse(
                content="",
                is_error=True,
                error_message=f"Error generating answer: {str(e)}"
            )