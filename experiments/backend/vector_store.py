from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
import ollama
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIRECTORY,
    SEPARATORS
)

class VectorStoreError(Exception):
    """Base exception class for vector store operations"""
    pass

class EmbeddingModelNotFoundError(VectorStoreError):
    """Raised when the embedding model is not available"""
    pass

class ChromaDBInitializationError(VectorStoreError):
    """Raised when ChromaDB fails to initialize"""
    pass

class VectorStore:
    def __init__(self, persist_directory: str = CHROMA_PERSIST_DIRECTORY):
        """
        Initialize the vector store with ChromaDB for storage.
        Creates a new collection if it doesn't exist, or uses existing one.
        
        Args:
            persist_directory: Directory where ChromaDB will store its data
        """
        try:
            # Initialize ChromaDB client with persistence
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
            
            # Always use get_or_create_collection instead of separate get/create
            self.collection = self.client.get_or_create_collection(
                name="document_chunks",
                metadata={"description": "Document chunks for RAG"}
            )
            
            # Initialize text splitter with configured parameters
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=SEPARATORS
            )
            
        except Exception as e:
            raise ChromaDBInitializationError(f"Failed to initialize ChromaDB: {str(e)}")

    def add_document(self, text: str, metadata: Optional[Dict] = None) -> None:
        """
        Process a document by splitting it into chunks and storing with embeddings.
        This method handles the entire process of document ingestion:
        1. Splits the document into manageable chunks
        2. Generates embeddings for each chunk using the Ollama model
        3. Stores the chunks and embeddings in ChromaDB
        
        Args:
            text: The document text to process
            metadata: Optional metadata to store with the chunks
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Generate embeddings for each chunk
            embeddings = []
            for chunk in chunks:
                try:
                    response = ollama.embeddings(
                        model=EMBEDDING_MODEL,
                        prompt=chunk
                    )
                    embeddings.append(response["embedding"])
                except Exception as e:
                    raise EmbeddingModelNotFoundError(
                        f"Failed to generate embeddings with model {EMBEDDING_MODEL}: {str(e)}"
                    )
            
            # Generate unique IDs for chunks
            ids = [str(uuid.uuid4()) for _ in chunks]
            
            # Clear existing content before adding new
            self.delete_all()
            
            # Add chunks and embeddings to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=chunks,
                ids=ids,
                metadatas=[metadata or {} for _ in chunks]
            )
        except Exception as e:
            if not isinstance(e, VectorStoreError):
                raise VectorStoreError(f"Failed to add document: {str(e)}")
            raise

    def get_relevant_chunks(self, query: str, k: int = 3) -> List[str]:
        """
        Retrieve the most relevant chunks for a query using embedding similarity.
        This method:
        1. Generates an embedding for the query
        2. Finds the most similar chunks in the vector store
        3. Returns the text of those chunks
        
        Args:
            query: The search query
            k: Number of chunks to retrieve
        
        Returns:
            List of relevant text chunks, ordered by relevance
        """
        try:
            # Generate embedding for the query
            query_embedding = ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt=query
            )["embedding"]
            
            # Query ChromaDB for similar chunks
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            return results["documents"][0]  # Return the text of the chunks
            
        except Exception as e:
            if not isinstance(e, VectorStoreError):
                raise VectorStoreError(f"Failed to retrieve chunks: {str(e)}")
            raise

    def delete_all(self) -> None:
        """
        Remove all documents from the collection.
        This method first retrieves all document IDs and then deletes them,
        which is the proper way to clear a ChromaDB collection.
        """
        try:
            # Get all document IDs in the collection
            all_ids = self.collection.get()["ids"]
            
            # If there are any documents, delete them
            if all_ids:
                self.collection.delete(ids=all_ids)
        except Exception as e:
            raise VectorStoreError(f"Failed to clear vector store: {str(e)}")

    def clear(self) -> None:
        """
        Alias for delete_all() to maintain compatibility with existing code.
        This method exists to provide a familiar interface while using
        the more robust delete_all() implementation underneath.
        """
        self.delete_all()

    def health_check(self) -> bool:
        """
        Check if the vector store is healthy and operational.
        Verifies that both ChromaDB and the embedding model are working.
        
        Returns:
            True if everything is working, raises exception otherwise
        """
        try:
            # Check if ChromaDB is responsive
            self.collection.count()
            
            # Check if embedding model is available
            ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt="test"
            )
            
            return True
        except Exception as e:
            raise VectorStoreError(f"Health check failed: {str(e)}")