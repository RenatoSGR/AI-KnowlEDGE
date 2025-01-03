from typing import List, Any, Tuple, Optional
import ollama
from ollama import chat

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

    def generate_summary(self, text: str, model_name: str) -> str:
        prompt = """Generate a summary of the text below.
        - If the text has a title, start with "Summary of [Title]:"
        - If no title is present, create a descriptive title and use it
        - Go straight into the summary content without any introductory phrases
        - Focus on key information and main points

        Text to summarize:
        """
        try:
            full_response = ""
            stream = chat(
                model=model_name,
                messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}],
                stream=True
            )
            for chunk in stream:
                if 'content' in chunk['message']:
                    full_response += chunk['message']['content']
            return full_response
        except Exception as e:
            raise Exception(f"Error generating summary: {e}")

    def generate_questions(self, text: str, model_name: str) -> List[str]:
        prompt = """Based on the following text, generate exactly three concise questions.
        Format each question on a new line, WITHOUT numbering or prefixes.
        Do not include any introductory text.
        Make each question standalone and thought-provoking.

        Text to analyze:
        """
        try:
            response = chat(
                model=model_name,
                messages=[{'role': 'user', 'content': f"{prompt}\n{text}"}]
            )
            questions = [q.strip() for q in response['message']['content'].splitlines() if q.strip()]
            return (questions + [''] * 3)[:3]
        except Exception as e:
            raise Exception(f"Error generating questions: {e}")

    def generate_answer(self, question: str, document_text: str, model_name: str) -> str:
        try:
            full_response = ""
            messages = [{'role': 'user', 'content': f"Answer the following question based on the document: {question}\n\n{document_text}"}]
            stream = chat(
                model=model_name,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if 'content' in chunk['message']:
                    full_response += chunk['message']['content']
            return full_response
        except Exception as e:
            raise Exception(f"Error generating answer: {e}")