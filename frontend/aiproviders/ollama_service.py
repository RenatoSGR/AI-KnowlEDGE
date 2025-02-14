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


    def generate_questions(self, model_name: str, summary: str) -> List[str]:
        response = requests.post(
            "http://localhost:8000/generate_questions/", json={"model_name": model_name, "content": summary}
        )

        questions = response.json()["questions"]

        return questions

    def generate_answer(
        self,
        question: str,
        relevant_chunks: List[str],
        model_name: str
    ) -> Generator[StreamResponse, None, None]:
        stream = requests.post(
            "http://localhost:8000/generate_answer", 
            json={"question": question, "relevant_chunks": relevant_chunks, "model_name": model_name}
        ).json()["answer"]
        
        first_chunk = True
        for chunk in stream:
            if 'content' in chunk['message']:
                response = StreamResponse(content=chunk['message']['content'])
                if first_chunk:
                    response.relevant_chunks = relevant_chunks
                    first_chunk = False
                yield response