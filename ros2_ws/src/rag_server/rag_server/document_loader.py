"""
Document Loader for RAG System
==============================
Loads knowledge base markdown documents, chunks them intelligently, 
and prepares them for embedding and vector database storage.

Author: Jayden Varghese George
Date: June 2026
Part of: RAG-Enhanced Elderly Care Robot Simulation
"""

from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """
    Represents a single chunk of a document with metadata.
    
    Attributes:
        chunk_id (str): Unique identifier for the chunk (format: {doc_id}_chunk_{index})
        content (str): The actual text content of the chunk
        metadata (dict): Dictionary containing source info, category, index, etc.
    """
    chunk_id: str
    content: str
    metadata: Dict[str, any]


class DocumentLoader:
    """
    Loads markdown documents from knowledge base and prepares them for RAG.
    
    This class:
    1. Discovers all .md files in knowledge_base directory
    2. Reads and processes document content
    3. Splits documents into semantic chunks
    4. Generates metadata for each chunk
    5. Returns structured data ready for embeddings and vector DB
    
    Configuration:
    - chunk_size: Target number of words per chunk (default: 500)
    - chunk_overlap: Number of overlapping words between chunks (default: 50)
    - min_chunk_size: Minimum words to avoid tiny chunks (default: 100)
    """
    
    def __init__(
        self, 
        kb_path: str = "./knowledge_base",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Initialize the DocumentLoader.
        
        Args:
            kb_path (str): Path to knowledge_base directory
            chunk_size (int): Target chunk size in words (default: 500)
            chunk_overlap (int): Overlap words between chunks (default: 50)
            min_chunk_size (int): Minimum chunk size to keep (default: 100)
        
        Raises:
            ValueError: If knowledge_base path doesn't exist
        """
        self.kb_path = Path(kb_path)
        
        # Validate path exists
        if not self.kb_path.exists():
            raise ValueError(f"Knowledge base path does not exist: {self.kb_path}")
        
        if not self.kb_path.is_dir():
            raise ValueError(f"Knowledge base path is not a directory: {self.kb_path}")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Statistics for tracking
        self.stats = {
            'total_files': 0,
            'total_chunks': 0,
            'total_words': 0,
            'failed_files': []
        }
        
        logger.info(f"DocumentLoader initialized with kb_path: {self.kb_path}")
        logger.info(f"Chunking config: size={chunk_size}, overlap={chunk_overlap}")
    
    def load_all_documents(self) -> List[DocumentChunk]:
        """
        Load all markdown documents from knowledge base and chunk them.
        
        Returns:
            List[DocumentChunk]: List of all document chunks with metadata
        
        Process:
            1. Find all .md files recursively in knowledge_base
            2. For each file, read content and extract metadata
            3. Split into chunks with overlap
            4. Return list of DocumentChunk objects
        """
        logger.info("Starting document loading...")
        chunks = []
        
        # Find all markdown files
        md_files = list(self.kb_path.rglob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files")
        
        if not md_files:
            logger.warning("No markdown files found in knowledge base!")
            return chunks
        
        # Process each file
        for md_file in md_files:
            try:
                file_chunks = self._process_file(md_file)
                chunks.extend(file_chunks)
                self.stats['total_files'] += 1
            except Exception as e:
                logger.error(f"Error processing {md_file}: {e}")
                self.stats['failed_files'].append(str(md_file))
                continue
        
        self.stats['total_chunks'] = len(chunks)
        
        # Log summary statistics
        logger.info(f"\n{'='*60}")
        logger.info(f"Document Loading Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Total files processed: {self.stats['total_files']}")
        logger.info(f"Total chunks created: {self.stats['total_chunks']}")
        logger.info(f"Total words loaded: {self.stats['total_words']:,}")
        if self.stats['failed_files']:
            logger.warning(f"Failed files: {len(self.stats['failed_files'])}")
            for f in self.stats['failed_files']:
                logger.warning(f"  - {f}")
        logger.info(f"{'='*60}\n")
        
        return chunks
    
    def _process_file(self, file_path: Path) -> List[DocumentChunk]:
        """
        Process a single markdown file into chunks.
        
        Args:
            file_path (Path): Path to the markdown file
        
        Returns:
            List[DocumentChunk]: List of chunks from this file
        """
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract category from file path (e.g., medications/hypertension_meds.md -> medications)
        relative_path = file_path.relative_to(self.kb_path)
        category = str(relative_path.parent) if relative_path.parent != Path('.') else 'root'
        
        # Document metadata (shared across all chunks from this file)
        base_metadata = {
            'source': str(relative_path),
            'category': category,
            'filename': file_path.name,
            'file_size_bytes': len(content),
            'loaded_at': datetime.now().isoformat(),
            'file_hash': self._hash_content(content)  # For deduplication detection
        }
        
        # Count words in document
        word_count = len(content.split())
        self.stats['total_words'] += word_count
        
        logger.info(f"Processing {relative_path} ({word_count} words)")
        
        # Split into chunks
        chunks = self._chunk_document(content, file_path.stem, base_metadata)
        
        return chunks
    
    def _chunk_document(
        self,
        content: str,
        doc_id: str,
        base_metadata: Dict
    ) -> List[DocumentChunk]:
        """
        Split document content into semantic chunks with overlap.
        
        Args:
            content (str): The full document text
            doc_id (str): Document identifier (used for chunk IDs)
            base_metadata (dict): Base metadata to include in all chunks
        
        Returns:
            List[DocumentChunk]: List of chunks with metadata
        
        Chunking Strategy:
            - Split on words (not characters) for semantic preservation
            - Add configurable overlap between chunks
            - Skip chunks smaller than min_chunk_size
            - Track chunk position in metadata
        """
        chunks = []
        words = content.split()
        
        if not words:
            logger.warning(f"Document {doc_id} is empty, skipping")
            return chunks
        
        # Calculate chunk boundaries (in word indices)
        step_size = self.chunk_size - self.chunk_overlap
        
        chunk_index = 0
        for start_idx in range(0, len(words), step_size):
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            
            # Skip chunks that are too small
            if len(chunk_words) < self.min_chunk_size:
                logger.debug(f"Skipping small chunk (size: {len(chunk_words)})")
                continue
            
            chunk_text = ' '.join(chunk_words)
            
            # Create unique chunk ID
            chunk_id = f"{doc_id}_chunk_{chunk_index:03d}"
            
            # Build metadata for this chunk
            chunk_metadata = {
                **base_metadata,
                'chunk_index': chunk_index,
                'chunk_position': f"{start_idx}-{end_idx}",
                'chunk_word_count': len(chunk_words),
                'is_overlapped': start_idx > 0  # True if this chunk overlaps with previous
            }
            
            # Create DocumentChunk object
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata
            )
            
            chunks.append(chunk)
            chunk_index += 1
        
        logger.debug(f"Created {chunk_index} chunks from {doc_id}")
        
        return chunks
    
    def _hash_content(self, content: str) -> str:
        """
        Generate SHA256 hash of content for deduplication.
        
        Args:
            content (str): The content to hash
        
        Returns:
            str: Hex digest of SHA256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def get_statistics(self) -> Dict:
        """
        Get loading statistics.
        
        Returns:
            dict: Statistics about loaded documents
        """
        return self.stats.copy()
    
    def load_documents_by_category(self, category: str) -> List[DocumentChunk]:
        """
        Load and chunk only documents from a specific category.
        
        Useful for loading subsets (e.g., only medications).
        
        Args:
            category (str): Category name (e.g., 'medications', 'elderly_care')
        
        Returns:
            List[DocumentChunk]: Chunks from specified category
        """
        logger.info(f"Loading documents from category: {category}")
        
        category_path = self.kb_path / category
        if not category_path.exists():
            logger.warning(f"Category path does not exist: {category_path}")
            return []
        
        chunks = []
        md_files = list(category_path.rglob("*.md"))
        
        for md_file in md_files:
            try:
                file_chunks = self._process_file(md_file)
                chunks.extend(file_chunks)
            except Exception as e:
                logger.error(f"Error processing {md_file}: {e}")
                continue
        
        logger.info(f"Loaded {len(chunks)} chunks from {category}")
        return chunks
    
    def export_chunks_to_dict(self, chunks: List[DocumentChunk]) -> List[Dict]:
        """
        Convert DocumentChunk objects to dictionaries (for JSON serialization, API responses).
        
        Args:
            chunks (List[DocumentChunk]): List of chunks to convert
        
        Returns:
            List[Dict]: List of chunk dictionaries
        """
        return [
            {
                'id': chunk.chunk_id,
                'content': chunk.content,
                'metadata': chunk.metadata
            }
            for chunk in chunks
        ]


# ============================================================================
# Utility Functions for Integration
# ============================================================================

def load_knowledge_base(
    kb_path: str = "./knowledge_base",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> Tuple[List[DocumentChunk], Dict]:
    """
    Convenience function to load entire knowledge base.
    
    Args:
        kb_path (str): Path to knowledge base
        chunk_size (int): Chunk size in words
        chunk_overlap (int): Overlap in words
    
    Returns:
        Tuple[List[DocumentChunk], Dict]: (chunks, statistics)
    """
    loader = DocumentLoader(kb_path, chunk_size, chunk_overlap)
    chunks = loader.load_all_documents()
    return chunks, loader.get_statistics()


if __name__ == "__main__":
    """
    Example usage of DocumentLoader.
    Run this script to test the loader with your knowledge base.
    """
    
    print("\n" + "="*70)
    print("RAG Document Loader - Test Run")
    print("="*70 + "\n")
    
    try:
        # Initialize loader
        loader = DocumentLoader(
            kb_path="./knowledge_base",
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Load all documents
        chunks = loader.load_all_documents()
        
        # Display summary
        stats = loader.get_statistics()
        print(f"\n✓ Successfully loaded {len(chunks)} chunks")
        print(f"✓ Statistics: {stats}")
        
        # Display first chunk as example
        if chunks:
            print(f"\n--- First Chunk Example ---")
            first = chunks[0]
            print(f"ID: {first.chunk_id}")
            print(f"Content preview: {first.content[:200]}...")
            print(f"Metadata: {first.metadata}")
        
        print("\n" + "="*70)
        print("✓ Document Loader Test Passed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
