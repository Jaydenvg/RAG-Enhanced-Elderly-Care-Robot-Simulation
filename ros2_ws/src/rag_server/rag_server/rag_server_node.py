"""
RAG Server Node for ROS2
========================
ROS2 node that loads knowledge base documents and prepares for semantic search.

Author: Jayden Varghese George
Date: June 2026
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
from pathlib import Path

from .document_loader import DocumentLoader


class RAGServerNode(Node):
    """
    ROS2 Node for RAG document retrieval.
    
    Loads knowledge base on startup and prepares for semantic search.
    
    Subscribers:
        /rag_query (String) - Incoming user queries
    
    Publishers:
        /rag_status (String) - System status updates
    
    Parameters:
        kb_path (str): Path to knowledge base directory
        chunk_size (int): Size of document chunks in words
        chunk_overlap (int): Overlap between chunks in words
    """
    
    def __init__(self):
        super().__init__('rag_server_node')
        
        # Declare and get parameters
        self.declare_parameter('kb_path', './knowledge_base')
        self.declare_parameter('chunk_size', 500)
        self.declare_parameter('chunk_overlap', 50)
        
        kb_path = self.get_parameter('kb_path').value
        chunk_size = self.get_parameter('chunk_size').value
        chunk_overlap = self.get_parameter('chunk_overlap').value
        
        self.get_logger().info("="*70)
        self.get_logger().info("RAG Server Node Initializing")
        self.get_logger().info("="*70)
        self.get_logger().info(f"Knowledge Base Path: {kb_path}")
        self.get_logger().info(f"Chunk Size: {chunk_size}")
        self.get_logger().info(f"Chunk Overlap: {chunk_overlap}")
        
        # Initialize document loader
        try:
            # Convert relative path to absolute if needed
            if not os.path.isabs(kb_path):
                kb_path = os.path.join(os.getcwd(), kb_path)
            
            self.loader = DocumentLoader(
                kb_path=kb_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            self.get_logger().info("✓ Document Loader initialized")
        except Exception as e:
            self.get_logger().error(f"✗ Failed to initialize DocumentLoader: {e}")
            raise
        
        # Load knowledge base
        try:
            self.chunks = self.loader.load_all_documents()
            self.stats = self.loader.get_statistics()
            
            self.get_logger().info(f"✓ Knowledge base loaded successfully")
            self.get_logger().info(f"  - Files processed: {self.stats['total_files']}")
            self.get_logger().info(f"  - Chunks created: {self.stats['total_chunks']}")
            self.get_logger().info(f"  - Total words: {self.stats['total_words']:,}")
            
            if self.stats['failed_files']:
                self.get_logger().warning(f"  - Failed files: {len(self.stats['failed_files'])}")
                for f in self.stats['failed_files']:
                    self.get_logger().warning(f"    - {f}")
        
        except Exception as e:
            self.get_logger().error(f"✗ Failed to load knowledge base: {e}")
            raise
        
        # Create publishers and subscribers
        self.status_pub = self.create_publisher(String, '/rag_status', 10)
        self.query_sub = self.create_subscription(
            String,
            '/rag_query',
            self.query_callback,
            10
        )
        
        self.get_logger().info("✓ Publishers and subscribers created")
        self.get_logger().info("="*70)
        self.get_logger().info("RAG Server Node Ready!")
        self.get_logger().info("="*70)
        
        # Publish startup status
        self._publish_status("RAG Server initialized successfully")
    
    def query_callback(self, msg: String):
        """
        Handle incoming queries.
        
        In Phase 2, this will perform semantic search.
        For now, logs the query and returns system info.
        
        Args:
            msg (String): Query message with data field
        """
        query = msg.data
        self.get_logger().info(f"Query received: '{query}'")
        
        # For Phase 1: Just acknowledge and provide system status
        response = {
            'query': query,
            'status': 'ready',
            'phase': 1,
            'message': 'Document loader ready. Semantic search (Phase 1 Week 3) coming soon.',
            'system_info': {
                'chunks_loaded': len(self.chunks),
                'total_words': self.stats['total_words'],
                'files_processed': self.stats['total_files']
            }
        }
        
        # Publish response
        status_msg = String(data=json.dumps(response))
        self.status_pub.publish(status_msg)
        self.get_logger().info(f"Response published to /rag_status")
    
    def _publish_status(self, message: str):
        """
        Publish a status message.
        
        Args:
            message (str): Status message to publish
        """
        status = {
            'timestamp': self.get_clock().now().to_msg().sec,
            'message': message,
            'chunks_available': len(self.chunks),
            'total_words': self.stats['total_words']
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
