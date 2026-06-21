"""
NLI Processor Node for Elderly Care Robot

ROS2 node that:
1. Subscribes to /patient_query (patient's natural language input)
2. Classifies intent using IntentClassifier
3. Extracts entities using EntityExtractor
4. Publishes structured NLI result to /nli_result
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import logging

from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLIProcessorNode(Node):
    """ROS2 Node for Natural Language Intent processing."""
    
    def __init__(self):
        """Initialize NLI Processor Node."""
        super().__init__('nli_processor_node')
        
        self.get_logger().info('Initializing NLI Processor Node...')
        
        # Initialize NLI components
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        
        # Create subscriber for patient queries (ROS2 syntax: just pass queue size as number)
        self.query_subscription = self.create_subscription(
            String,
            '/patient_query',
            self.query_callback,
            10  # Queue size (ROS2 style, not queue_size=10)
        )
        
        # Create publisher for NLI results
        self.nli_result_publisher = self.create_publisher(
            String,
            '/nli_result',
            10  # Queue size
        )
        
        # Statistics
        self.query_count = 0
        self.intent_distribution = {}
        
        self.get_logger().info('✓ NLI Processor Node initialized')
        self.get_logger().info('✓ Listening on /patient_query')
        self.get_logger().info('✓ Publishing to /nli_result')
    
    def query_callback(self, msg: String):
        """
        Callback function for incoming patient queries.
        
        This method is called every time a message is received on /patient_query.
        It processes the query through intent classification and entity extraction,
        then publishes the results as JSON to /nli_result.
        """
        query = msg.data
        self.query_count += 1
        
        self.get_logger().info(f'[Query #{self.query_count}] Received: "{query}"')
        
        try:
            # Classify intent
            intent, confidence = self.intent_classifier.classify(query)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(query)
            
            # Update statistics
            if intent not in self.intent_distribution:
                self.intent_distribution[intent] = 0
            self.intent_distribution[intent] += 1
            
            # Build NLI result
            nli_result = {
                'query': query,
                'intent': intent,
                'confidence': float(confidence),
                'entities': entities,
                'query_number': self.query_count
            }
            
            # Log the result
            self.get_logger().info(
                f"Intent: {intent} | Confidence: {confidence:.2f} | "
                f"Medications: {entities['medications']} | "
                f"Conditions: {entities['conditions']}"
            )
            
            # Publish result as JSON
            result_msg = String(data=json.dumps(nli_result))
            self.nli_result_publisher.publish(result_msg)
        
        except Exception as e:
            self.get_logger().error(f"Error processing query: {str(e)}")
    
    def get_statistics(self) -> dict:
        """Get processing statistics."""
        return {
            'total_queries_processed': self.query_count,
            'intent_distribution': self.intent_distribution
        }


def main(args=None):
    """Main entry point for NLI Processor Node."""
    rclpy.init(args=args)
    nli_node = NLIProcessorNode()
    
    try:
        rclpy.spin(nli_node)
    except KeyboardInterrupt:
        nli_node.get_logger().info('Shutting down...')
    finally:
        nli_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
