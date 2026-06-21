"""
RAG Document Loader - Config Integration
=========================================
Shows how to integrate the DocumentLoader with your RAG config (rag_config.yaml)
and how to use it within the ROS2 rag_server_node.

Author: Jayden Varghese George
Date: June 2026
"""

import yaml
from pathlib import Path
from typing import Dict, Optional
import logging

from .document_loader import DocumentLoader, DocumentChunk

logger = logging.getLogger(__name__)


class RAGConfig:
    """
    Reads and manages RAG configuration from YAML file.
    
    Expected config file structure (rag_config.yaml):
```yaml
    knowledge_base:
      path: ./knowledge_base
    
    document_loader:
      chunk_size: 500
      chunk_overlap: 50
      min_chunk_size: 100
    
    embedding:
      model: sentence-transformers/all-MiniLM-L6-v2
      dimension: 384
    
    vector_db:
      type: chroma
      path: ./data/chroma_db
      collection_name: healthcare_kb
    
    retrieval:
      top_k: 3
      similarity_threshold: 0.6
```
    """
    
    def __init__(self, config_path: str = "./config/rag_config.yaml"):
        """
        Initialize RAG config from YAML file.
        
        Args:
            config_path (str): Path to rag_config.yaml
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is malformed
        """
        self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        if not self.config:
            raise ValueError("Config file is empty or malformed")
        
        logger.info(f"RAG Config loaded from {config_path}")
    
    def get_kb_path(self) -> str:
        """Get knowledge base path from config."""
        return self.config.get('knowledge_base', {}).get('path', './knowledge_base')
    
    def get_chunk_size(self) -> int:
        """Get document chunk size from config."""
        return self.config.get('document_loader', {}).get('chunk_size', 500)
    
    def get_chunk_overlap(self) -> int:
        """Get chunk overlap from config."""
        return self.config.get('document_loader', {}).get('chunk_overlap', 50)
    
    def get_min_chunk_size(self) -> int:
        """Get minimum chunk size from config."""
        return self.config.get('document_loader', {}).get('min_chunk_size', 100)
    
    def get_embedding_model(self) -> str:
        """Get embedding model name from config."""
        return self.config.get('embedding', {}).get('model', 
                                                   'sentence-transformers/all-MiniLM-L6-v2')
    
    def get_vector_db_path(self) -> str:
        """Get vector database path from config."""
        return self.config.get('vector_db', {}).get('path', './data/chroma_db')
    
    def get_collection_name(self) -> str:
        """Get Chroma collection name from config."""
        return self.config.get('vector_db', {}).get('collection_name', 'healthcare_kb')
    
    def get_top_k(self) -> int:
        """Get top-k retrieval parameter from config."""
        return self.config.get('retrieval', {}).get('top_k', 3)
    
    def get_similarity_threshold(self) -> float:
        """Get similarity threshold from config."""
        return self.config.get('retrieval', {}).get('similarity_threshold', 0.6)


class ConfiguredDocumentLoader:
    """
    DocumentLoader wrapper that reads config from rag_config.yaml.
    
    This is the recommended way to use DocumentLoader in your ROS2 project,
    as it ensures all components use consistent configuration.
    """
    
    def __init__(self, config_path: str = "./config/rag_config.yaml"):
        """
        Initialize DocumentLoader using RAG config.
        
        Args:
            config_path (str): Path to rag_config.yaml
        """
        self.config = RAGConfig(config_path)
        
        # Initialize DocumentLoader with config parameters
        self.loader = DocumentLoader(
            kb_path=self.config.get_kb_path(),
            chunk_size=self.config.get_chunk_size(),
            chunk_overlap=self.config.get_chunk_overlap(),
            min_chunk_size=self.config.get_min_chunk_size()
        )
        
        logger.info("ConfiguredDocumentLoader initialized with RAG config")
    
    def load_knowledge_base(self) -> tuple:
        """
        Load knowledge base using config parameters.
        
        Returns:
            Tuple[List[DocumentChunk], Dict]: (chunks, statistics)
        """
        chunks = self.loader.load_all_documents()
        stats = self.loader.get_statistics()
        return chunks, stats
    
    def load_category(self, category: str) -> list:
        """
        Load specific knowledge base category.
        
        Args:
            category (str): Category name (e.g., 'medications')
        
        Returns:
            List[DocumentChunk]: Chunks from that category
        """
        return self.loader.load_documents_by_category(category)
    
    def get_config(self):
        """Get the underlying RAG config object."""
        return self.config


if __name__ == "__main__":
    """
    Example of using ConfiguredDocumentLoader.
    
    Run with:
        python config_integration.py
    
    Make sure you have:
        1. config/rag_config.yaml (with proper paths)
        2. knowledge_base/ directory with markdown files
    """
    
    print("\n" + "="*70)
    print("RAG Document Loader - Config Integration Example")
    print("="*70 + "\n")
    
    try:
        # Initialize with config
        doc_loader = ConfiguredDocumentLoader(
            config_path="./config/rag_config.yaml"
        )
        
        # Get config object for inspection
        config = doc_loader.get_config()
        print("Configuration loaded:")
        print(f"  KB Path: {config.get_kb_path()}")
        print(f"  Chunk Size: {config.get_chunk_size()}")
        print(f"  Chunk Overlap: {config.get_chunk_overlap()}")
        print(f"  Embedding Model: {config.get_embedding_model()}")
        print(f"  Vector DB Path: {config.get_vector_db_path()}")
        print()
        
        # Load knowledge base
        print("Loading knowledge base...")
        chunks, stats = doc_loader.load_knowledge_base()
        
        print(f"\n✓ Successfully loaded {len(chunks)} chunks")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total words: {stats['total_words']:,}")
        
        # Display some chunks
        if chunks:
            print(f"\nFirst 3 chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"\n  Chunk {i+1}: {chunk.chunk_id}")
                print(f"    Category: {chunk.metadata['category']}")
                print(f"    Words: {chunk.metadata['chunk_word_count']}")
                print(f"    Preview: {chunk.content[:80]}...")
        
        # Load specific category
        print("\n" + "-"*70)
        print("Loading specific category (medications)...")
        med_chunks = doc_loader.load_category("medications")
        print(f"✓ Loaded {len(med_chunks)} medication chunks")
        
        print("\n" + "="*70)
        print("✓ Integration test passed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
