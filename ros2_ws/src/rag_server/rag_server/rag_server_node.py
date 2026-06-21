"""
RAG Server Node for ROS2
========================
ROS2 node that performs semantic search over knowledge base documents.

Author: Jayden Varghese George
Date: June 2026
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
from pathlib import Path

from .retriever import RAGRetriever


class RAGServerNode(Node):
    """
    ROS2 Node for RAG semantic search.
    
    Loads knowledge base, builds vector index, and performs semantic search.
    
    Subscribers:
        /rag_query (String) - Incoming user queries
    
    Publishers:
        /rag_status (String) - System status updates
        /rag_results (String) - Search results
    
    Parameters:
        kb_path (str): Path to knowledge base directory
        db_path (str): Path to vector database storage
        chunk_size (int): Size of document chunks in words
        chunk_overlap (int): Overlap between chunks in words
        top_k (int): Number of results to return per query
        similarity_threshold (float): Minimum similarity score
    """
    
    def __init__(self):
        super().__init__('rag_server_node')
        
        # Declare parameters
        self.declare_parameter('kb_path', './knowledge_base')
        self.declare_parameter('db_path', './data/chroma_db')
        self.declare_parameter('chunk_size', 500)
        self.declare_parameter('chunk_overlap', 50)
        self.declare_parameter('top_k', 3)
        self.declare_parameter('similarity_threshold', 0.0)
        
        # Get parameters
        kb_path = self.get_parameter('kb_path').value
        db_path = self.get_parameter('db_path').value
        chunk_size = self.get_parameter('chunk_size').value
        chunk_overlap = self.get_parameter('chunk_overlap').value
        self.top_k = self.get_parameter('top_k').value
        self.similarity_threshold = self.get_parameter('similarity_threshold').value
        
        self.get_logger().info("="*70)
        self.get_logger().info("RAG Server Node - Phase 1 Week 3 (Semantic Search)")
        self.get_logger().info("="*70)
        self.get_logger().info(f"Knowledge Base Path: {kb_path}")
        self.get_logger().info(f"Vector DB Path: {db_path}")
        self.get_logger().info(f"Chunk Size: {chunk_size}")
        self.get_logger().info(f"Top K Results: {self.top_k}")
        
        # Initialize RAG retriever
        try:
            # Convert relative paths to absolute if needed
            if not os.path.isabs(kb_path):
                kb_path = os.path.join(os.getcwd(), kb_path)
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.getcwd(), db_path)
            
            self.get_logger().info("Initializing RAG Retriever (this may take a moment)...")
            self.retriever = RAGRetriever(
                kb_path=kb_path,
                db_path=db_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                rebuild_db=False
            )
            self.get_logger().info("✓ RAG Retriever initialized")
            
        except Exception as e:
            self.get_logger().error(f"✗ Failed to initialize RAG Retriever: {e}")
            raise
        
        # Get statistics
        try:
            stats = self.retriever.get_statistics()
            self.get_logger().info(f"✓ System ready")
            self.get_logger().info(f"  - Files loaded: {stats['knowledge_base']['total_files']}")
            self.get_logger().info(f"  - Chunks created: {stats['knowledge_base']['total_chunks']}")
            self.get_logger().info(f"  - Words indexed: {stats['knowledge_base']['total_words']:,}")
            self.get_logger().info(f"  - Documents indexed: {stats['vector_database']['indexed_documents']}")
            self.stats = stats
        except Exception as e:
            self.get_logger().error(f"✗ Failed to get statistics: {e}")
            raise
        
        # Create publishers and subscribers
        self.status_pub = self.create_publisher(String, '/rag_status', 10)
        self.results_pub = self.create_publisher(String, '/rag_results', 10)
        self.query_sub = self.create_subscription(
            String,
            '/rag_query',
            self.query_callback,
            10
        )
        
        self.get_logger().info("✓ Publishers and subscribers created")
        self.get_logger().info("="*70)
        self.get_logger().info("RAG Server Node Ready for Queries!")
        self.get_logger().info("="*70)
        
        # Publish startup status
        self._publish_status("RAG Server with semantic search ready")
    
    def query_callback(self, msg: String):
        """
        Handle incoming queries with semantic search.
        
        Args:
            msg (String): Query message with data field
        """
        query = msg.data
        self.get_logger().info(f"Query received: '{query}'")
        
        try:
            # Perform semantic search
            results = self.retriever.search(
                query=query,
                top_k=self.top_k,
                similarity_threshold=self.similarity_threshold
            )
            
            # Format response
            response = {
                'query': query,
                'status': 'success',
                'phase': 1,
                'week': 3,
                'num_results': len(results),
                'results': [
                    {
                        'similarity': result['similarity'],
                        'source': result['source'],
                        'category': result['category'],
                        'preview': result['document'][:200] + '...' if len(result['document']) > 200 else result['document']
                    }
                    for result in results
                ],
                'system_info': {
                    'chunks_indexed': self.stats['vector_database']['indexed_documents'],
                    'embedding_dimension': self.stats['vector_database']['embedding_dimension']
                }
            }
            
            # Publish results
            results_msg = String(data=json.dumps(response))
            self.results_pub.publish(results_msg)
            
            self.get_logger().info(f"✓ Found {len(results)} results, published to /rag_results")
            
        except Exception as e:
            self.get_logger().error(f"✗ Search failed: {e}")
            
            # Publish error response
            error_response = {
                'query': query,
                'status': 'error',
                'error': str(e),
                'num_results': 0,
                'results': []
            }
            
            results_msg = String(data=json.dumps(error_response))
            self.results_pub.publish(results_msg)
    
    def _publish_status(self, message: str):
        """
        Publish a status message.
        
        Args:
            message (str): Status message to publish
        """
        status = {
            'message': message,
            'phase': 1,
            'week': 3,
            'chunks_available': self.stats['knowledge_base']['total_chunks'],
            'total_words': self.stats['knowledge_base']['total_words']
        }
        msg = String(data=json.dumps(status))
        self.status_pub.publish(msg)


def main(args=None):
    """Main entry point for ROS2 node."""
    rclpy.init(args=args)
    node = RAGServerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

