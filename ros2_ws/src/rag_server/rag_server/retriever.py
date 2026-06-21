"""
RAG Retriever - Semantic Search Interface
==========================================
High-level interface combining document loading, embeddings, and vector search.

Author: Jayden Varghese George
Date: June 2026
Part of: RAG-Enhanced Elderly Care Robot Simulation
"""

import logging
from typing import List, Dict, Optional
import os

from .document_loader import DocumentLoader, DocumentChunk
from .vector_db import VectorDB
from .embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Complete RAG (Retrieval-Augmented Generation) retriever pipeline.
    
    Combines:
    1. Document loading (markdown files)
    2. Chunking (semantic segments with overlap)
    3. Embeddings (vector representations)
    4. Vector search (semantic similarity retrieval)
    
    Usage:
        retriever = RAGRetriever(kb_path="./knowledge_base")
        results = retriever.search("What are side effects?", top_k=3)
    """
    
    def __init__(
        self,
        kb_path: str = "./knowledge_base",
        db_path: str = "./data/chroma_db",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        rebuild_db: bool = False
    ):
        """
        Initialize the RAG retriever.
        
        Args:
            kb_path (str): Path to knowledge base directory
            db_path (str): Path to vector database storage
            chunk_size (int): Document chunk size in words
            chunk_overlap (int): Overlap between chunks in words
            embedding_model (str): Sentence-Transformers model name
            rebuild_db (bool): Force rebuild of vector database
        
        Raises:
            Exception: If initialization fails
        """
        logger.info("="*70)
        logger.info("Initializing RAG Retriever")
        logger.info("="*70)
        
        self.kb_path = kb_path
        self.db_path = db_path
        self.rebuild_db = rebuild_db
        
        # Initialize document loader
        try:
            logger.info(f"Initializing DocumentLoader (kb_path={kb_path})")
            self.loader = DocumentLoader(
                kb_path=kb_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            logger.info("✓ DocumentLoader initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DocumentLoader: {e}")
            raise
        
        # Initialize vector database
        try:
            logger.info(f"Initializing VectorDB (db_path={db_path})")
            self.vector_db = VectorDB(
                db_path=db_path,
                embedding_model=embedding_model
            )
            logger.info("✓ VectorDB initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {e}")
            raise
        
        # Check if we need to rebuild the database
        self.is_indexed = self._check_db_status()
        
        if rebuild_db or not self.is_indexed:
            logger.info("Building/rebuilding vector database...")
            self._build_database()
        else:
            logger.info("✓ Using existing vector database")
        
        logger.info("="*70)
        logger.info("RAG Retriever Ready!")
        logger.info("="*70)
    
    def _check_db_status(self) -> bool:
        """
        Check if vector database is already built.
        
        Returns:
            bool: True if database exists and has documents
        """
        try:
            self.vector_db.init_collection("healthcare_kb")
            info = self.vector_db.get_collection_info()
            
            if info and info.get('document_count', 0) > 0:
                logger.info(f"Found existing database with {info['document_count']} documents")
                return True
            else:
                logger.info("Database exists but is empty")
                return False
        except Exception as e:
            logger.info(f"No existing database found: {e}")
            return False
    
    def _build_database(self) -> None:
        """
        Build the vector database from knowledge base documents.
        
        Process:
        1. Load all documents from knowledge base
        2. Generate embeddings for each chunk
        3. Store in ChromaDB
        """
        try:
            logger.info("Loading documents from knowledge base...")
            chunks = self.loader.load_all_documents()
            
            if not chunks:
                logger.warning("No documents loaded from knowledge base!")
                return
            
            logger.info(f"Loaded {len(chunks)} chunks from {self.loader.stats['total_files']} files")
            
            # Initialize collection
            self.vector_db.init_collection("healthcare_kb")
            
            # Delete existing collection to rebuild
            if self.rebuild_db:
                try:
                    self.vector_db.delete_collection()
                    self.vector_db.init_collection("healthcare_kb")
                except:
                    pass
            
            # Add documents to vector database
            logger.info("Adding documents to vector database...")
            self.vector_db.add_documents(chunks)
            
            logger.info("✓ Vector database built successfully")
            self.is_indexed = True
            
        except Exception as e:
            logger.error(f"Failed to build database: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Semantic search over the knowledge base.
        
        Args:
            query (str): User query
            top_k (int): Number of results to return
            similarity_threshold (float): Minimum similarity score (0.0-1.0)
        
        Returns:
            List[Dict]: Retrieved chunks with metadata and similarity scores
                Format: [
                    {
                        'document': str,
                        'source': str,
                        'category': str,
                        'similarity': float,
                        'metadata': dict
                    },
                    ...
                ]
        
        Example:
            >>> results = retriever.search("What are side effects?", top_k=3)
            >>> for result in results:
            ...     print(f"{result['similarity']:.2f}: {result['document'][:50]}...")
        """
        if not self.is_indexed:
            logger.warning("Database not indexed. Cannot search.")
            return []
        
        if not query or not isinstance(query, str):
            logger.warning("Invalid query provided")
            return []
        
        try:
            logger.info(f"Searching for: '{query}'")
            
            # Search vector database
            raw_results = self.vector_db.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            # Format results with extracted metadata
            formatted_results = []
            for result in raw_results:
                formatted_result = {
                    'document': result['document'],
                    'similarity': result['similarity'],
                    'source': result['metadata'].get('source', 'unknown'),
                    'category': result['metadata'].get('category', 'unknown'),
                    'metadata': result['metadata']
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"✓ Found {len(formatted_results)} relevant results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the knowledge base and index.
        
        Returns:
            dict: Statistics including file count, chunk count, word count
        """
        loader_stats = self.loader.get_statistics()
        db_info = self.vector_db.get_collection_info()
        
        return {
            'knowledge_base': {
                'total_files': loader_stats['total_files'],
                'total_chunks': loader_stats['total_chunks'],
                'total_words': loader_stats['total_words'],
            },
            'vector_database': {
                'collection_name': db_info.get('collection_name', 'N/A'),
                'indexed_documents': db_info.get('document_count', 0),
                'embedding_dimension': db_info.get('embedding_dimension', 0),
            },
            'status': {
                'is_indexed': self.is_indexed,
                'ready': self.is_indexed and loader_stats['total_files'] > 0
            }
        }


if __name__ == "__main__":
    """
    Test the RAG retriever.
    Run with: python retriever.py
    """
    
    print("\n" + "="*70)
    print("RAG Retriever - Test Run")
    print("="*70 + "\n")
    
    try:
        # Initialize retriever
        print("Initializing RAG Retriever...")
        retriever = RAGRetriever(
            kb_path="./knowledge_base",
            db_path="./data/chroma_db",
            rebuild_db=False  # Use existing DB if available
        )
        
        # Get statistics
        stats = retriever.get_statistics()
        print("\n✓ Knowledge Base Statistics:")
        print(f"  Files: {stats['knowledge_base']['total_files']}")
        print(f"  Chunks: {stats['knowledge_base']['total_chunks']}")
        print(f"  Words: {stats['knowledge_base']['total_words']:,}")
        print(f"  Indexed: {stats['vector_database']['indexed_documents']}")
        
        # Test searches
        test_queries = [
            "What are the side effects of lisinopril?",
            "How can I prevent falls in elderly patients?",
            "What medications treat high blood pressure?"
        ]
        
        print("\n✓ Test Searches:")
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = retriever.search(query, top_k=2)
            
            for i, result in enumerate(results, 1):
                print(f"  Result {i} ({result['similarity']:.2f} similarity):")
                print(f"    Category: {result['category']}")
                print(f"    Preview: {result['document'][:70]}...")
        
        print("\n" + "="*70)
        print("✓ RAG Retriever Test Passed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
