import re


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