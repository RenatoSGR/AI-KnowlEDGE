from typing import List, Any, Tuple, Optional, Generator
from dataclasses import dataclass
import ollama
from ollama import chat
import re

@dataclass
class StreamResponse:
    content: str
    is_error: bool = False
    error_message: Optional[str] = None

class OllamaService:
    def __init__(self):
        self._available_models: Optional[List[str]] = None
        self.TOKEN_THRESHOLD = 2500  # Updated token threshold

    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation based on common rules:
        - ~4 characters per token for English text
        - Split on whitespace for words
        - Count punctuation separately
        """
        if not text:
            return 0
            
        # Count words (splitting on whitespace)
        words = text.split()
        # Count punctuation marks that are likely their own tokens
        punctuation = len(re.findall(r'[.,!?;:"]', text))
        # Special characters and numbers often count as separate tokens
        special_chars = len(re.findall(r'[@#$%^&*()<>{}\[\]~`_\-+=|\\]', text))
        # Numbers often count as their own tokens
        numbers = len(re.findall(r'\d+', text))
        
        # Rough estimation combining all factors
        estimated_tokens = len(words) + punctuation + special_chars + numbers
        return estimated_tokens

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
        Generates a summary using a custom map-reduce approach.
        """
        try:
            # Check token count and decide whether to chunk
            estimated_tokens = self._estimate_tokens(text)
            
            if estimated_tokens <= self.TOKEN_THRESHOLD:
                # If text is small enough, summarize directly
                prompt = """Summarize the following text. Focus on key information and main points:

                {text}

                Summary:"""
                
                stream = ollama.chat(
                    model=model_name,
                    messages=[{
                        'role': 'user',
                        'content': prompt.format(text=text)
                    }],
                    stream=True
                )
                
                for chunk in stream:
                    if 'content' in chunk['message']:
                        yield StreamResponse(content=chunk['message']['content'])
                return

            # For longer texts, use map-reduce approach
            chunks = self._split_text(text)
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

    def generate_questions(self, text: str, model_name: str, summary: str) -> List[str]:
        """
        Generates questions based on the document summary.
        The generated questions will be answered using the full document text.
        """
        try:
            few_shot_prompt = """Given a summary, generate exactly three insightful questions.  generated questions will be answered using the full document textThe. Follow these examples precisely:

Example 1:
Summary: The report analyzes the global coffee industry in 2023, highlighting a 15% increase in sustainable farming practices, significant price fluctuations due to weather events in Brazil, and emerging trends in specialty coffee consumption across Asia.

How did extreme weather conditions in Brazil impact global coffee prices and supply chains?
What specific sustainable farming practices saw the highest adoption rates among coffee producers?
Which Asian markets showed the most significant growth in specialty coffee consumption and why?

Example 2:
Summary: The study examines remote work productivity during 2020-2023, finding that 65% of companies maintained or increased productivity, while noting challenges in collaboration and mental health. New hybrid work models emerged as a preferred solution across various industries.

What specific factors contributed to maintaining or increasing productivity in remote work settings?
How did companies successfully address collaboration challenges in the remote work environment?
What were the key characteristics of the most effective hybrid work models implemented?

Now, generate three questions for this summary:

{summary}"""
            
            messages = [{'role': 'user', 'content': few_shot_prompt.format(summary=summary)}]
            
            response = chat(model=model_name, messages=messages)
            # Skip any lines that aren't questions (like "Questions:" headers)
            questions = [
                line.strip() for line in response['message']['content'].splitlines()
                if line.strip() and line.strip().endswith('?')
            ]
            return (questions + [''] * 3)[:3]  # Ensure exactly 3 questions
            
        except Exception as e:
            raise Exception(f"Error generating questions: {e}")

    def generate_answer(self, question: str, document_text: str, model_name: str) -> Generator[StreamResponse, None, None]:
        """
        Generates a detailed answer using the complete document text.
        """
        try:
            messages = [{'role': 'user', 'content': f"""Answer the following question with all relevant details from the document:

            Question: {question}

            Document text: {document_text}"""}]
            
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