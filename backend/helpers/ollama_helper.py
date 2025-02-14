import re
import ollama

from typing import List, Any, Tuple, Optional, Generator, Dict
from collections.abc import Iterator
from ollama._types import ChatResponse


EMBEDDING_MODEL = "nomic-embed-text:latest"
EXCLUDED_MODELS = {EMBEDDING_MODEL} 
# Text Processing
SEPARATORS = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
# Model Configuration
TOKEN_THRESHOLD = 2500  # For deciding when to use map-reduce summarization


def get_nb_tokens(text: str) -> int:
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

    return str(len(words) + punctuation + special_chars + numbers)


def get_available_models() -> List[str]:
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
    

def split_text(text: str, chunk_size: int = 2000) -> List[str]:
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


def generate_questions(model_name: str, summary: str) -> List[str]:
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
        question: str,
        relevant_chunks: List[str],
        model_name: str
    ) -> Iterator[ChatResponse]:
    
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

    response = ollama.chat(model=model_name, messages=messages, stream=True)

    return response
