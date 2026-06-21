"""
Embeddings Service for RAG System
==================================
Converts document chunks into vector embeddings using Sentence-Transformers.

Author: Jayden Varghese George
Date: June 2026
Part of: RAG-Enhanced Elderly Care Robot Simulation
"""

import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Generates embeddings for documents and queries using Sentence-Transformers.
    
    Uses the 'all-MiniLM-L6-v2' model which:
    - Produces 384-dimensional embeddings
    - Fast inference (suitable for real-time applications)
    - Good quality for semantic similarity tasks
    - Efficient (lightweight for edge/robot deployment)
    
    Model info:
    - Parameters: ~22M
    - Dimensions: 384
    - Max sequence length: 256 tokens (~1000 words)
    - Inference time: ~5-10ms per chunk on CPU
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embeddings service.
        
        Args:
            model_name (str): HuggingFace model identifier
                Default: all-MiniLM-L6-v2 (384-dimensional embeddings)
        
        Raises:
            Exception: If model download/initialization fails
        """
        logger.info(f"Initializing EmbeddingsService with model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"✓ Model loaded successfully")
            logger.info(f"  - Embedding dimension: {self.embedding_dim}")
            logger.info(f"  - Max sequence length: {self.model.max_seq_length}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def embed_text(self, text: str, convert_to_numpy: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text (str): Text to embed
            convert_to_numpy (bool): Return as numpy array (default: True)
        
        Returns:
            np.ndarray: Embedding vector (1D array of size embedding_dim)
        
        Example:
            >>> service = EmbeddingsService()
            >>> embedding = service.embed_text("What are side effects?")
            >>> embedding.shape
            (384,)
        """
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided to embed_text")
            return np.zeros(self.embedding_dim)
        
        embedding = self.model.encode(text, convert_to_numpy=convert_to_numpy)
        return embedding
    
    def embed_texts(self, texts: List[str], convert_to_numpy: bool = True) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts (List[str]): List of texts to embed
            convert_to_numpy (bool): Return as numpy array (default: True)
        
        Returns:
            np.ndarray: Embedding matrix (shape: [len(texts), embedding_dim])
        
        Example:
            >>> service = EmbeddingsService()
            >>> texts = ["Document 1", "Document 2", "Document 3"]
            >>> embeddings = service.embed_texts(texts)
            >>> embeddings.shape
            (3, 384)
        """
        if not texts or not isinstance(texts, list):
            logger.warning("Empty or invalid texts list provided to embed_texts")
            return np.zeros((len(texts) if isinstance(texts, list) else 0, self.embedding_dim))
        
        embeddings = self.model.encode(texts, convert_to_numpy=convert_to_numpy)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.
        
        Returns:
            int: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        return self.embedding_dim
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including name, dimension, max length
        """
        return {
            'model_name': self.model.modules()[0].auto_model.config.model_type,
            'embedding_dimension': self.embedding_dim,
            'max_sequence_length': self.model.max_seq_length,
            'num_parameters': sum(p.numel() for p in self.model.parameters()),
        }


# ============================================================================
# Utility Function
# ============================================================================

def embed_documents(
    texts: List[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> tuple:
    """
    Convenience function to embed a list of documents.
    
    Args:
        texts (List[str]): List of document texts
        model_name (str): Model to use (default: all-MiniLM-L6-v2)
    
    Returns:
        Tuple[np.ndarray, EmbeddingsService]: (embeddings, service)
    
    Example:
        >>> texts = ["doc1", "doc2", "doc3"]
        >>> embeddings, service = embed_documents(texts)
        >>> embeddings.shape
        (3, 384)
    """
    service = EmbeddingsService(model_name)
    embeddings = service.embed_texts(texts)
    return embeddings, service


if __name__ == "__main__":
    """
    Test the embeddings service.
    Run with: python embeddings.py
    """
    
    print("\n" + "="*70)
    print("Embeddings Service - Test Run")
    print("="*70 + "\n")
    
    try:
        # Initialize service
        service = EmbeddingsService()
        
        # Test single embedding
        query = "What are the side effects of lisinopril?"
        query_embedding = service.embed_text(query)
        print(f"✓ Single text embedding:")
        print(f"  Query: '{query}'")
        print(f"  Embedding shape: {query_embedding.shape}")
        print(f"  First 10 values: {query_embedding[:10]}")
        
        # Test batch embeddings
        documents = [
            "Lisinopril is an ACE inhibitor used to treat high blood pressure.",
            "Common side effects include dizziness and dry cough.",
            "Patient education about medication compliance is important."
        ]
        
        doc_embeddings = service.embed_texts(documents)
        print(f"\n✓ Batch text embeddings:")
        print(f"  Documents: {len(documents)}")
        print(f"  Embedding matrix shape: {doc_embeddings.shape}")
        
        # Test similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarity = cosine_similarity([query_embedding], doc_embeddings)[0]
        print(f"\n✓ Similarity scores:")
        for i, (doc, score) in enumerate(zip(documents, similarity)):
            print(f"  Doc {i+1}: {score:.4f} - '{doc[:50]}...'")
        
        # Show model info
        info = service.get_model_info()
        print(f"\n✓ Model information:")
        print(f"  Embedding dimension: {info['embedding_dimension']}")
        print(f"  Max sequence length: {info['max_sequence_length']}")
        
        print("\n" + "="*70)
        print("✓ Embeddings Service Test Passed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
