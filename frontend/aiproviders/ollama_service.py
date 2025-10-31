import requests

from typing import List, Optional, Generator
from dataclasses import dataclass, field

from .config import TOKEN_THRESHOLD


@dataclass
class StreamResponse:
    """
    Represents a streaming response from the language model.
    This class helps structure the responses and handle potential errors.
    """
    content: str
    is_error: bool = False
    error_message: Optional[str] = None
    relevant_chunks: List[str] = field(default_factory=list)


class OllamaService:
    def __init__(self):
        self._available_models: Optional[List[str]] = None
        self.TOKEN_THRESHOLD = TOKEN_THRESHOLD

    def _estimate_tokens(self, text: str) -> int:
        response = requests.post("http://localhost:8000/estimate_tokens/", json={"content": text})
        nb_tokens = int(response.json()["nb_tokens"])
        return nb_tokens

    @property
    def available_models(self) -> List[str]:
        if self._available_models is None:
            self._available_models = self._get_available_models()
        return self._available_models

    def _get_available_models(self) -> List[str]:
        generation_models = requests.get("http://localhost:8000/get_models/").json()["available_models"]
        return generation_models

    def get_best_model(self) -> Optional[str]:
        """Get the best available model optimized for memory usage"""
        try:
            response = requests.get("http://localhost:8000/get_best_model/")
            if response.status_code == 200:
                return response.json()["best_model"]
            return None
        except Exception as e:
            print(f"Error getting best model: {e}")
            # Fallback to first available model
            models = self.available_models
            return models[0] if models else None


    def generate_questions(self, model_name: str, summary: str) -> List[str]:
        # Use best available model if no model specified or model is problematic
        if not model_name:
            model_name = self.get_best_model()
            
        try:
            response = requests.post(
                "http://localhost:8000/generate_questions/", 
                json={"model_name": model_name, "content": summary}
            )
            
            if response.status_code == 200:
                questions = response.json()["questions"]
                return questions
            else:
                # If the request failed, try with the best available model
                best_model = self.get_best_model()
                if best_model and best_model != model_name:
                    response = requests.post(
                        "http://localhost:8000/generate_questions/", 
                        json={"model_name": best_model, "content": summary}
                    )
                    if response.status_code == 200:
                        return response.json()["questions"]
                
                # Return generic questions if all else fails
                return [
                    "What are the main topics covered in this document?",
                    "What are the key insights or findings?", 
                    "What are the important takeaways?"
                ]
                
        except Exception as e:
            print(f"Error generating questions: {e}")
            # Return generic questions as fallback
            return [
                "What are the main topics covered in this document?",
                "What are the key insights or findings?", 
                "What are the important takeaways?"
            ]

    def generate_answer(
        self,
        question: str,
        relevant_chunks: List[str],
        model_name: str
    ) -> Generator[StreamResponse, None, None]:
        # Use best available model if no model specified
        if not model_name:
            model_name = self.get_best_model()
            
        try:
            response = requests.post(
                "http://localhost:8000/generate_answer", 
                json={"question": question, "relevant_chunks": relevant_chunks, "model_name": model_name}
            )
            
            if response.status_code != 200:
                # Try with best available model if the request failed
                best_model = self.get_best_model()
                if best_model and best_model != model_name:
                    response = requests.post(
                        "http://localhost:8000/generate_answer", 
                        json={"question": question, "relevant_chunks": relevant_chunks, "model_name": best_model}
                    )
                
                if response.status_code != 200:
                    yield StreamResponse(
                        content="I apologize, but I'm currently experiencing technical difficulties. Please try again later.",
                        is_error=True,
                        error_message="Model unavailable due to memory constraints"
                    )
                    return
            
            stream = response.json()["answer"]
            
            first_chunk = True
            for chunk in stream:
                if 'content' in chunk['message']:
                    response = StreamResponse(content=chunk['message']['content'])
                    if first_chunk:
                        response.relevant_chunks = relevant_chunks
                        first_chunk = False
                    yield response
                    
        except Exception as e:
            print(f"Error generating answer: {e}")
            yield StreamResponse(
                content="I apologize, but I encountered an error while generating the answer. Please try again.",
                is_error=True,
                error_message=str(e)
            )