import re
import ollama
import time
import logging

from typing import List, Any, Tuple, Optional, Generator, Dict
from collections.abc import Iterator
from ollama._types import ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


EMBEDDING_MODEL = "nomic-embed-text:latest"
# Fallback models in order of preference (smaller models first for memory efficiency)
PREFERRED_MODELS = ["llama3.2:1b", "gemma2:2b", "phi3:latest"]
EXCLUDED_MODELS = {EMBEDDING_MODEL} 
# Text Processing
SEPARATORS = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
# Model Configuration
TOKEN_THRESHOLD = 2500  # For deciding when to use map-reduce summarization
MAX_RETRIES = 3  # Number of retries for model operations
RETRY_DELAY = 1  # Delay between retries in seconds


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
        logger.error(f"Error retrieving models: {e}")
        return []


def get_best_available_model() -> Optional[str]:
    """
    Get the best available model for text generation, prioritizing smaller models
    for better memory efficiency in resource-constrained environments.
    
    Returns:
        The name of the best available model, or None if no models are available
    """
    try:
        available_models = get_available_models()
        if not available_models:
            logger.warning("No models available")
            return None
            
        # Check for preferred models in order of preference (smallest first)
        for preferred_model in PREFERRED_MODELS:
            if preferred_model in available_models:
                logger.info(f"Using preferred model: {preferred_model}")
                return preferred_model
        
        # If no preferred models are available, use the first available model
        model = available_models[0]
        logger.info(f"Using fallback model: {model}")
        return model
        
    except Exception as e:
        logger.error(f"Error selecting best model: {e}")
        return None


def test_model_memory(model_name: str) -> bool:
    """
    Test if a model can be loaded and used without memory issues.
    
    Args:
        model_name: Name of the model to test
        
    Returns:
        True if the model works, False if there are memory issues
    """
    try:
        # Simple test with minimal prompt
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Hi'}],
            options={'num_predict': 1}  # Limit to 1 token to minimize memory usage
        )
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'memory' in error_msg or 'gpu' in error_msg or 'unable to load' in error_msg:
            logger.warning(f"Model {model_name} has memory issues: {e}")
            return False
        # Re-raise other types of errors
        raise e
    

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
    # Use fallback model if the provided model is None or has issues
    if not model_name:
        model_name = get_best_available_model()
        if not model_name:
            raise Exception("No suitable model available for question generation")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Test model memory first
            if not test_model_memory(model_name):
                logger.warning(f"Model {model_name} failed memory test, trying fallback")
                model_name = get_best_available_model()
                if not model_name:
                    raise Exception("No suitable model available after memory test")
                continue
                    
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
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'num_predict': 500,  # Limit output length to save memory
                    'temperature': 0.7,   # Balanced creativity
                    'top_p': 0.9         # Focus on most likely tokens
                }
            )

            # Extract questions from response
            questions = [
                line.strip() for line in response['message']['content'].splitlines()
                if line.strip() and line.strip().endswith('?')
            ]

            # Ensure exactly three questions
            if len(questions) >= 3:
                return questions[:3]
            elif len(questions) > 0:
                # Pad with generic questions if we don't have enough
                generic_questions = [
                    "What are the main points discussed in this document?",
                    "What are the key findings or conclusions?",
                    "What implications or recommendations are presented?"
                ]
                return (questions + generic_questions)[:3]
            else:
                # If no questions were extracted, return generic ones
                return [
                    "What are the main topics covered in this document?",
                    "What are the key insights or findings?",
                    "What are the important takeaways?"
                ]

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Attempt {attempt + 1} failed for model {model_name}: {e}")
            
            # Check for memory-related errors
            if 'memory' in error_msg or 'gpu' in error_msg or 'unable to load' in error_msg:
                logger.warning(f"Memory issue detected with {model_name}, trying fallback model")
                # Try to get a different model
                available_models = get_available_models()
                if available_models:
                    # Remove the problematic model and try the next one
                    if model_name in available_models:
                        available_models.remove(model_name)
                    if available_models:
                        model_name = available_models[0]
                        logger.info(f"Switching to fallback model: {model_name}")
                        continue
                        
            # For the last attempt, raise the exception
            if attempt == MAX_RETRIES - 1:
                raise Exception(f"Error generating questions after {MAX_RETRIES} attempts: {e}")
            
            # Wait before retry
            time.sleep(RETRY_DELAY)
    
    # This should never be reached, but just in case
    raise Exception("Failed to generate questions after all attempts")
    

def generate_answer(
        question: str,
        relevant_chunks: List[str],
        model_name: str
    ) -> Iterator[ChatResponse]:
    
    # Use fallback model if the provided model is None or has issues
    if not model_name:
        model_name = get_best_available_model()
        if not model_name:
            raise Exception("No suitable model available for answer generation")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Test model memory first
            if not test_model_memory(model_name):
                logger.warning(f"Model {model_name} failed memory test, trying fallback")
                model_name = get_best_available_model()
                if not model_name:
                    raise Exception("No suitable model available after memory test")
                continue
            
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

            response = ollama.chat(
                model=model_name, 
                messages=messages, 
                stream=True,
                options={
                    'num_predict': 1000,  # Limit output length to save memory
                    'temperature': 0.3,    # Lower temperature for more focused answers
                    'top_p': 0.9          # Focus on most likely tokens
                }
            )

            return response
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Attempt {attempt + 1} failed for model {model_name}: {e}")
            
            # Check for memory-related errors
            if 'memory' in error_msg or 'gpu' in error_msg or 'unable to load' in error_msg:
                logger.warning(f"Memory issue detected with {model_name}, trying fallback model")
                # Try to get a different model
                available_models = get_available_models()
                if available_models:
                    # Remove the problematic model and try the next one
                    if model_name in available_models:
                        available_models.remove(model_name)
                    if available_models:
                        model_name = available_models[0]
                        logger.info(f"Switching to fallback model: {model_name}")
                        continue
                        
            # For the last attempt, raise the exception
            if attempt == MAX_RETRIES - 1:
                raise Exception(f"Error generating answer after {MAX_RETRIES} attempts: {e}")
            
            # Wait before retry
            time.sleep(RETRY_DELAY)
    
    # This should never be reached, but just in case
    raise Exception("Failed to generate answer after all attempts")
