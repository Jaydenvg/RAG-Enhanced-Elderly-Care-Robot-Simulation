"""
Vector Database Interface for RAG System
=========================================
Manages ChromaDB for storing and retrieving document embeddings.

Author: Jayden Varghese George
Date: June 2026
Part of: RAG-Enhanced Elderly Care Robot Simulation
"""

import logging
import os
from typing import List, Dict, Optional
import chromadb

from .embeddings import EmbeddingsService
from .document_loader import DocumentChunk

logger = logging.getLogger(__name__)


class VectorDB:
    """
    Interface to ChromaDB vector database.
    
    Handles:
    - Connection to ChromaDB
    - Collection creation/management
    - Document indexing (storing embeddings)
    - Semantic search queries
    
    ChromaDB features used:
    - Persistent storage (DuckDB + Parquet)
    - HNSW indexing for fast similarity search
    - Cosine distance metric (good for embeddings)
    """
    
    def __init__(
        self,
        db_path: str = "./data/chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize vector database.
        
        Args:
            db_path (str): Path to ChromaDB persistent storage
            embedding_model (str): Model for generating embeddings
        
        Raises:
            Exception: If database initialization fails
        """
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        logger.info(f"Initializing VectorDB at: {db_path}")
        
        try:
            # Initialize ChromaDB client with persistent storage (new API)
            self.client = chromadb.PersistentClient(path=db_path)
            logger.info("✓ ChromaDB client initialized")
            
            # Initialize embeddings service
            self.embeddings_service = EmbeddingsService(embedding_model)
            logger.info("✓ Embeddings service initialized")
            
            self.collection = None
            self.collection_name = None
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {e}")
            raise
    
    def init_collection(
        self,
        collection_name: str = "healthcare_kb",
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Initialize or get a collection in the database.
        
        Args:
            collection_name (str): Name of the collection
            metadata (dict): Metadata for the collection
        
        Raises:
            Exception: If collection creation fails
        """
        try:
            # Get or create collection (new API doesn't require metadata for HNSW)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or {"hnsw:space": "cosine"}
            )
            
            self.collection_name = collection_name
            logger.info(f"✓ Collection '{collection_name}' ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def add_documents(
        self,
        chunks: List[DocumentChunk],
        batch_size: int = 100
    ) -> None:
        """
        Add document chunks to the vector database.
        
        Process:
        1. Extract text content from chunks
        2. Generate embeddings for all chunks
        3. Store embeddings + metadata in ChromaDB
        4. Batch processing for memory efficiency
        
        Args:
            chunks (List[DocumentChunk]): Chunks to add (from DocumentLoader)
            batch_size (int): Process chunks in batches (default: 100)
        
        Raises:
            Exception: If indexing fails
        """
        if not self.collection:
            raise ValueError("Collection not initialized. Call init_collection() first.")
        
        if not chunks:
            logger.warning("No chunks to add to database")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to vector database...")
        
        try:
            # Process in batches for memory efficiency
            for batch_start in range(0, len(chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]
                
                # Extract data from chunks
                ids = [chunk.chunk_id for chunk in batch_chunks]
                documents = [chunk.content for chunk in batch_chunks]
                metadatas = [chunk.metadata for chunk in batch_chunks]
                
                # Generate embeddings
                embeddings = self.embeddings_service.embed_texts(documents)
                
                # Add to ChromaDB
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),  # Convert numpy to list for ChromaDB
                    documents=documents,
                    metadatas=metadatas
                )
                
                logger.info(f"  Added batch {batch_start//batch_size + 1} ({batch_end} total chunks)")
            
            logger.info(f"✓ Successfully indexed {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Semantic search in the vector database.
        
        Process:
        1. Generate embedding for query
        2. Search ChromaDB for nearest neighbors
        3. Convert distances to similarity scores
        4. Filter by threshold if specified
        5. Return ranked results
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return (default: 3)
            similarity_threshold (float): Minimum similarity score (default: 0.0)
        
        Returns:
            List[Dict]: Search results with documents, metadata, and similarity scores
                Format: [{'document': str, 'metadata': dict, 'similarity': float}, ...]
        
        Example:
            >>> results = vector_db.search("What are side effects?", top_k=3)
            >>> results[0]['similarity']
            0.87
        """
        if not self.collection:
            raise ValueError("Collection not initialized. Call init_collection() first.")
        
        if not query or not isinstance(query, str):
            logger.warning("Invalid query provided to search()")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_service.embed_text(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            if not results['documents'] or not results['documents'][0]:
                logger.info(f"No results found for query: '{query}'")
                return []
            
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            # Convert cosine distances to similarity scores
            # ChromaDB returns distances; similarity = 1 - distance for cosine
            similarities = [1 - d for d in distances]
            
            # Filter by threshold and build result list
            filtered_results = []
            for doc, meta, sim in zip(documents, metadatas, similarities):
                if sim >= similarity_threshold:
                    filtered_results.append({
                        'document': doc,
                        'metadata': meta,
                        'similarity': round(sim, 4)  # Round to 4 decimal places
                    })
            
            logger.info(f"✓ Found {len(filtered_results)} results for: '{query[:50]}...'")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_collection(self) -> None:
        """
        Delete the current collection (useful for re-indexing).
        
        Args:
            None
        """
        if self.collection_name:
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = None
                logger.info(f"✓ Collection '{self.collection_name}' deleted")
            except Exception as e:
                logger.error(f"Failed to delete collection: {e}")
                raise
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the current collection.
        
        Returns:
            dict: Collection statistics including count of documents
        """
        if not self.collection:
            return {}
        
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_dimension': self.embeddings_service.get_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def persist(self) -> None:
        """
        Persist data to disk (ChromaDB handles this automatically).
        """
        try:
            logger.info("✓ Vector database persisted to disk")
        except Exception as e:
            logger.warning(f"Could not persist database: {e}")


if __name__ == "__main__":
    """
    Test the vector database.
    Run with: python vector_db.py
    """
    
    print("\n" + "="*70)
    print("Vector Database - Test Run")
    print("="*70 + "\n")
    
    try:
        # Initialize database
        db = VectorDB(db_path="./data/test_chroma_db")
        db.init_collection("test_collection")
        
        # Create test chunks
        from document_loader import DocumentChunk
        
        test_chunks = [
            DocumentChunk(
                chunk_id="test_001",
                content="Lisinopril is an ACE inhibitor medication for blood pressure.",
                metadata={'source': 'test.md', 'category': 'medications'}
            ),
            DocumentChunk(
                chunk_id="test_002",
                content="Common side effects include dizziness, dry cough, and fatigue.",
                metadata={'source': 'test.md', 'category': 'medications'}
            ),
            DocumentChunk(
                chunk_id="test_003",
                content="Fall prevention is crucial for elderly patients.",
                metadata={'source': 'test.md', 'category': 'elderly_care'}
            ),
        ]
        
        # Add to database
        db.add_documents(test_chunks)
        
        # Get info
        info = db.get_collection_info()
        print(f"✓ Collection info: {info}")
        
        # Test search
        query = "What are the side effects?"
        results = db.search(query, top_k=2)
        
        print(f"\n✓ Search results for: '{query}'")
        for i, result in enumerate(results):
            print(f"\n  Result {i+1}:")
            print(f"    Similarity: {result['similarity']}")
            print(f"    Document: {result['document'][:60]}...")
            print(f"    Source: {result['metadata']['source']}")
        
        print("\n" + "="*70)
        print("✓ Vector Database Test Passed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
