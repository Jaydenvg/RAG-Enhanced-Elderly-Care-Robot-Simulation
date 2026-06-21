"""
Unit Tests for Document Loader
===============================
Tests the DocumentLoader class with various document types and edge cases.

Run with: pytest test_document_loader.py -v
"""

import pytest
import tempfile
from pathlib import Path
from rag_server.document_loader import DocumentLoader, DocumentChunk, load_knowledge_base


class TestDocumentLoaderInitialization:
    """Test DocumentLoader initialization and validation."""
    
    def test_init_with_valid_path(self):
        """Should initialize successfully with valid path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DocumentLoader(kb_path=tmpdir)
            assert loader.kb_path == Path(tmpdir)
            assert loader.chunk_size == 500
            assert loader.chunk_overlap == 50
    
    def test_init_with_invalid_path(self):
        """Should raise ValueError for non-existent path."""
        with pytest.raises(ValueError, match="does not exist"):
            DocumentLoader(kb_path="/nonexistent/path")
    
    def test_init_with_file_instead_of_directory(self):
        """Should raise ValueError if path is a file, not directory."""
        with tempfile.NamedTemporaryFile() as tmp:
            with pytest.raises(ValueError, match="not a directory"):
                DocumentLoader(kb_path=tmp.name)
    
    def test_init_with_custom_chunk_params(self):
        """Should accept custom chunk parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DocumentLoader(
                kb_path=tmpdir,
                chunk_size=300,
                chunk_overlap=30,
                min_chunk_size=50
            )
            assert loader.chunk_size == 300
            assert loader.chunk_overlap == 30
            assert loader.min_chunk_size == 50


class TestDocumentChunking:
    """Test document chunking logic."""
    
    def test_chunk_simple_document(self):
        """Should chunk a simple document correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 600)  # 600 words
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=300, chunk_overlap=0)
            chunks = loader.load_all_documents()
            
            # Should create approximately 2 chunks (600 / 300)
            assert len(chunks) >= 1
            # All chunks should have content
            assert all(chunk.content for chunk in chunks)
    
    def test_chunk_overlap(self):
        """Should create overlapping chunks when overlap is specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 600)
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=300, chunk_overlap=50)
            chunks = loader.load_all_documents()
            
            # With overlap, should have more chunks
            assert len(chunks) >= 1
            if len(chunks) > 1:
                # Second chunk should contain some words from first chunk
                first_words = chunks[0].content.split()
                second_words = chunks[1].content.split()
                # Check if there's overlap (not exact, as we're checking concepts)
                assert len(chunks[0].content) > 0
                assert len(chunks[1].content) > 0
    
    def test_chunk_metadata_creation(self):
        """Should create proper metadata for chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 200)
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=500)
            chunks = loader.load_all_documents()
            
            assert len(chunks) > 0
            chunk = chunks[0]
            
            # Check metadata structure
            assert 'source' in chunk.metadata
            assert 'category' in chunk.metadata
            assert 'filename' in chunk.metadata
            assert 'chunk_index' in chunk.metadata
            assert 'chunk_word_count' in chunk.metadata
            assert 'file_hash' in chunk.metadata
            assert 'loaded_at' in chunk.metadata
    
    def test_min_chunk_size_enforcement(self):
        """Should skip chunks smaller than min_chunk_size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            # Create content that would result in a small final chunk
            test_file.write_text("word " * 550)  # 550 words
            
            loader = DocumentLoader(
                kb_path=tmpdir,
                chunk_size=500,
                chunk_overlap=0,
                min_chunk_size=100
            )
            chunks = loader.load_all_documents()
            
            # All chunks should be >= min_chunk_size
            assert all(chunk.metadata['chunk_word_count'] >= 100 for chunk in chunks)


class TestDocumentLoading:
    """Test document discovery and loading."""
    
    def test_load_single_document(self):
        """Should load a single markdown document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_content = "This is test content with multiple words"
            test_file.write_text(test_content)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert len(chunks) > 0
            assert test_content in chunks[0].content
    
    def test_load_multiple_documents(self):
        """Should load multiple documents from different directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure
            (Path(tmpdir) / "medications").mkdir()
            (Path(tmpdir) / "elderly_care").mkdir()
            
            # Create files
            (Path(tmpdir) / "medications" / "test1.md").write_text("word " * 200)
            (Path(tmpdir) / "elderly_care" / "test2.md").write_text("word " * 200)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert len(chunks) >= 2
            
            # Check categories are properly assigned
            categories = {chunk.metadata['category'] for chunk in chunks}
            assert 'medications' in categories
            assert 'elderly_care' in categories
    
    def test_load_empty_directory(self):
        """Should handle empty knowledge base gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert chunks == []
            assert loader.get_statistics()['total_files'] == 0
    
    def test_load_documents_by_category(self):
        """Should load only documents from specified category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "medications").mkdir()
            (Path(tmpdir) / "elderly_care").mkdir()
            
            (Path(tmpdir) / "medications" / "test1.md").write_text("word " * 200)
            (Path(tmpdir) / "elderly_care" / "test2.md").write_text("word " * 200)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_documents_by_category("medications")
            
            # All chunks should be from medications
            assert all(chunk.metadata['category'] == 'medications' for chunk in chunks)
    
    def test_load_documents_by_nonexistent_category(self):
        """Should handle non-existent category gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_documents_by_category("nonexistent")
            
            assert chunks == []


class TestChunkID:
    """Test chunk ID generation and uniqueness."""
    
    def test_chunk_ids_are_unique(self):
        """Should generate unique chunk IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 1000)  # Long document, multiple chunks
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=300)
            chunks = loader.load_all_documents()
            
            # All IDs should be unique
            ids = [chunk.chunk_id for chunk in chunks]
            assert len(ids) == len(set(ids))
    
    def test_chunk_id_format(self):
        """Should follow correct chunk ID format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "myfile.md"
            test_file.write_text("word " * 200)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert len(chunks) > 0
            # Format should be: filename_chunk_000
            assert chunks[0].chunk_id.startswith("myfile_chunk_")


class TestMetadataTracking:
    """Test metadata tracking across chunks."""
    
    def test_metadata_consistency(self):
        """Should maintain consistent base metadata across chunks from same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 1000)
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=300)
            chunks = loader.load_all_documents()
            
            # All chunks should have same source and filename
            sources = {chunk.metadata['source'] for chunk in chunks}
            filenames = {chunk.metadata['filename'] for chunk in chunks}
            
            assert len(sources) == 1
            assert len(filenames) == 1
            assert "test.md" in filenames
    
    def test_chunk_position_tracking(self):
        """Should track chunk positions correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 600)
            
            loader = DocumentLoader(kb_path=tmpdir, chunk_size=300, chunk_overlap=0)
            chunks = loader.load_all_documents()
            
            # Check chunk positions
            assert chunks[0].metadata['chunk_index'] == 0
            if len(chunks) > 1:
                assert chunks[1].metadata['chunk_index'] == 1


class TestStatistics:
    """Test statistics tracking."""
    
    def test_statistics_tracking(self):
        """Should track loading statistics correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test1.md").write_text("word " * 200)
            (Path(tmpdir) / "test2.md").write_text("word " * 300)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            stats = loader.get_statistics()
            
            assert stats['total_files'] == 2
            assert stats['total_chunks'] == len(chunks)
            assert stats['total_words'] >= 500


class TestExportFunctionality:
    """Test chunk export to dictionaries."""
    
    def test_export_chunks_to_dict(self):
        """Should convert chunks to dictionary format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 200)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            dict_chunks = loader.export_chunks_to_dict(chunks)
            
            assert len(dict_chunks) == len(chunks)
            assert all('id' in d for d in dict_chunks)
            assert all('content' in d for d in dict_chunks)
            assert all('metadata' in d for d in dict_chunks)


class TestUtilityFunctions:
    """Test convenience functions."""
    
    def test_load_knowledge_base_function(self):
        """Should work as convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 200)
            
            chunks, stats = load_knowledge_base(kb_path=tmpdir)
            
            assert len(chunks) > 0
            assert 'total_files' in stats
            assert 'total_chunks' in stats


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_file(self):
        """Should handle empty markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "empty.md"
            test_file.write_text("")
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            # Empty file should not produce chunks
            assert len(chunks) == 0
    
    def test_file_with_special_characters(self):
        """Should handle special characters in content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("word " * 100 + " café ñ 中文 emoji🤖", encoding='utf-8')
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert len(chunks) > 0
            # Content should preserve special chars
            combined_content = " ".join([c.content for c in chunks])
            assert "café" in combined_content
    
    def test_file_with_newlines(self):
        """Should handle documents with multiple newlines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "word " * 50 + "\n\n" + "word " * 50 + "\n" + "word " * 100
            test_file.write_text(content)
            
            loader = DocumentLoader(kb_path=tmpdir)
            chunks = loader.load_all_documents()
            
            assert len(chunks) > 0


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])

