import ollama
import requests

from typing import List, Any, Tuple, Optional, Generator, Dict
from dataclasses import dataclass, field

from ollama import chat
from .config import EXCLUDED_MODELS, TOKEN_THRESHOLD


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
        """
        Generates an answer using RAG with retrieved context chunks.
        This is the core of the RAG implementation for question answering.
        """
        try:
            # Format context with chunk numbering
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"[Context {i}]: {chunk}")
            context = "\n\n".join(context_parts)

            messages = [{
                'role': 'user',
                'content': f"""Answer the following question using ONLY the provided context.
                If the answer cannot be fully determined from the context, acknowledge this
                and explain what can be determined from the available information.

                Question: {question}

                Relevant context:
                {context}

                Answer:"""
            }]

            stream = ollama.chat(model=model_name, messages=messages, stream=True)

            # Yield the relevant chunks along with the first response
            first_chunk = True
            for chunk in stream:
                if 'content' in chunk['message']:
                    response = StreamResponse(content=chunk['message']['content'])
                    if first_chunk:
                        response.relevant_chunks = relevant_chunks  # Add chunks to the first response
                        first_chunk = False
                    yield response

        except Exception as e:
            yield StreamResponse(
                content="",
                is_error=True,
                error_message=f"Error generating answer: {str(e)}"
            )