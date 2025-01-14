from typing import List, Any, Tuple, Optional, Generator, Dict
from dataclasses import dataclass, field
import ollama
from ollama import chat
import re
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
    """
    Manages interactions with Ollama models for text generation.
    Handles model selection, text generation, summarization, and question answering.
    """

    def __init__(self):
        """Initialize the Ollama service with default settings."""
        self._available_models: Optional[List[str]] = None
        self.TOKEN_THRESHOLD = TOKEN_THRESHOLD

    def _estimate_tokens(self, text: str) -> int:
        """
        Provides a rough estimation of tokens in a text string.
        This helps in deciding when to chunk text for processing.
        """
        if not text:
            return 0

        # Count various text elements that typically correspond to tokens
        words = text.split()
        punctuation = len(re.findall(r'[.,!?;:"]', text))
        special_chars = len(re.findall(r'[@#$%^&*()<>{}\[\]~`_\-+=|\\]', text))
        numbers = len(re.findall(r'\d+', text))

        return len(words) + punctuation + special_chars + numbers

    @property
    def available_models(self) -> List[str]:
        """
        Retrieves and caches the list of available models for text generation.
        Uses lazy loading to fetch models only when needed.
        """
        if self._available_models is None:
            self._available_models = self._get_available_models()
        return self._available_models

    def _get_available_models(self) -> List[str]:
        """
        Retrieve a list of available Ollama models for text generation.

        This method efficiently filters models during the initial extraction using
        the EXCLUDED_MODELS set from our configuration. This combines efficiency
        (filtering during extraction) with maintainability (centralized configuration).
        """
        try:
            items: List[Tuple[str, Any]] = ollama.list()

            # Extract and filter models in a single pass, using our configuration
            generation_models = [
                model.model
                for item in items
                if isinstance(item, tuple) and item[0] == 'models'
                for model in item[1]
                if model.model not in EXCLUDED_MODELS
            ]

            return generation_models
        except Exception as e:
            print(f"Error retrieving models: {e}")
            return []

    def _split_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """
        Splits text into smaller chunks while trying to maintain context.
        Uses paragraph and sentence boundaries for natural splits.
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            if len(paragraph) > chunk_size:
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
        Generates a document summary using a map-reduce approach for longer texts.
        For shorter texts, generates summary directly.
        """
        try:
            estimated_tokens = self._estimate_tokens(text)

            # Use direct summarization for shorter texts
            if estimated_tokens <= self.TOKEN_THRESHOLD:
                messages = [{
                    'role': 'user',
                    'content': f"""Create a comprehensive summary of the following text.
                    Focus on the key information and main points:

                    {text}

                    Summary:"""
                }]

                stream = ollama.chat(model=model_name, messages=messages, stream=True)

                for chunk in stream:
                    if 'content' in chunk['message']:
                        yield StreamResponse(content=chunk['message']['content'])
                return

            # For longer texts, use map-reduce approach
            chunks = self._split_text(text)
            chunk_summaries = []

            # Map phase: Summarize each chunk
            for chunk in chunks:
                response = ollama.chat(
                    model=model_name,
                    messages=[{
                        'role': 'user',
                        'content': f"Summarize this text extract:\n\n{chunk}"
                    }]
                )
                chunk_summaries.append(response['message']['content'])

            # Reduce phase: Combine summaries
            combined_text = "\n\n".join(chunk_summaries)
            stream = ollama.chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': f"""Combine these summaries into a single coherent summary.
                    Maintain a clear narrative flow and eliminate redundancy:

                    {combined_text}

                    Final Summary:"""
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

    def generate_questions(self, model_name: str, summary: str) -> List[str]:
        """
        Generates insightful questions based on the document summary.
        Returns exactly three questions that can be answered using the full document.
        """
        try:
            prompt = f"""Based on this document, create three specific and insightful questions
            that can be answered.

            ---

            Summary: {summary}

            Requirements:
            - Generate exactly three questions
            - Questions should require detailed answers from the full text provided
            - Focus on the most important aspects of the document
            - Make questions specific rather than general
            - The questions are supposed to be different from each other

            Questions:"""

            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )

            # Extract questions from response
            questions = [
                line.strip() for line in response['message']['content'].splitlines()
                if line.strip() and line.strip().endswith('?')
            ]

            # Ensure exactly three questions
            return (questions + [''] * 3)[:3]

        except Exception as e:
            print(f"Error generating questions: {e}")
            raise Exception(f"Error generating questions: {e}")

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