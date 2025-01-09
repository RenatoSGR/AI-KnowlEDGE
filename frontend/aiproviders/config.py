# RAG Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
NUM_CHUNKS_TO_RETRIEVE = 3
EMBEDDING_MODEL = "nomic-embed-text:latest"
EXCLUDED_MODELS = {EMBEDDING_MODEL}  # Use a set for efficient lookups
CHROMA_PERSIST_DIRECTORY = "./.chroma"

# Text Processing
SEPARATORS = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]

# Model Configuration
TOKEN_THRESHOLD = 2500  # For deciding when to use map-reduce summarization