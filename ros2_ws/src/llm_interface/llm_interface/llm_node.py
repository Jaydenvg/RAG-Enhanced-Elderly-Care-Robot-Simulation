"""
LLM Inference Node for Elderly Care Robot

This ROS2 node handles the complete LLM inference pipeline:

Flow:
1. Subscribe to /nli_result (from NLI Processor)
2. Subscribe to /rag_results (from RAG Server)
3. Wait for both NLI and RAG data
4. Build context-aware prompt using PromptBuilder
5. Generate response using Phi-2 model via ModelLoader
6. Publish structured response to /llm_response

Topics:
- Input:  /nli_result (JSON: intent, entities, confidence)
- Input:  /rag_results (JSON: retrieved documents, similarity scores)
- Output: /llm_response (JSON: response, metadata, timing)

This node is the bridge between understanding (NLI), 
retrieval (RAG), and generation (LLM).
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import logging
import time
from typing import Optional, Dict, Any

from .model_loader import LLMModelLoader
from .prompt_builder import PromptBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMInferenceNode(Node):
    """
    ROS2 Node for LLM-based response generation.
    
    This node combines NLI (intent/entities) and RAG (context)
    to generate informed responses using the Phi-2 LLM.
    """
    
    def __init__(self):
        """Initialize the LLM Inference Node."""
        super().__init__('llm_inference_node')
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('Initializing LLM Inference Node...')
        self.get_logger().info('=' * 60)
        
        # Initialize LLM components
        self.get_logger().info('Step 1: Initializing PromptBuilder...')
        self.prompt_builder = PromptBuilder()
        self.get_logger().info('✅ PromptBuilder initialized')
        
        self.get_logger().info('Step 2: Loading Phi-2 model (this may take 30-60 seconds)...')
        self.model_loader = LLMModelLoader()
        try:
            self.model_loader.load_model()
            self.get_logger().info('✅ Phi-2 model loaded successfully!')
            self.model_loaded = True
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load model: {str(e)}')
            self.get_logger().warn('Continuing without model - responses will be disabled')
            self.model_loaded = False
        
        # Storage for latest messages
        self.latest_nli_result: Optional[Dict] = None
        self.latest_rag_result: Optional[Dict] = None
        
        # Statistics
        self.query_count = 0
        self.successful_responses = 0
        self.failed_responses = 0
        self.total_inference_time = 0.0
        
        # Configure inference parameters
        self.max_tokens = self.declare_parameter('max_tokens', 256).value
        self.temperature = self.declare_parameter('temperature', 0.7).value
        self.top_p = self.declare_parameter('top_p', 0.95).value
        
        self.get_logger().info(f'Inference parameters:')
        self.get_logger().info(f'  - max_tokens: {self.max_tokens}')
        self.get_logger().info(f'  - temperature: {self.temperature}')
        self.get_logger().info(f'  - top_p: {self.top_p}')
        
        # Create subscribers (ROS2 syntax: just pass queue size as number)
        self.get_logger().info('Step 3: Creating ROS2 subscribers and publishers...')
        
        self.nli_subscription = self.create_subscription(
            String,
            '/nli_result',
            self.nli_callback,
            10  # Queue size (ROS2 style)
        )
        self.get_logger().info('✅ Subscribed to /nli_result')
        
        self.rag_subscription = self.create_subscription(
            String,
            '/rag_results',
            self.rag_callback,
            10  # Queue size
        )
        self.get_logger().info('✅ Subscribed to /rag_results')
        
        # Create publisher
        self.response_publisher = self.create_publisher(
            String,
            '/llm_response',
            10  # Queue size
        )
        self.get_logger().info('✅ Publisher to /llm_response created')
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('LLM Inference Node ready!')
        self.get_logger().info('Waiting for NLI and RAG results...')
        self.get_logger().info('=' * 60)
    
    def nli_callback(self, msg: String):
        """
        Callback for NLI results.
        
        Stores the latest NLI result and triggers inference
        if both NLI and RAG data are available.
        """
        try:
            self.latest_nli_result = json.loads(msg.data)
            self.get_logger().info(
                f"📥 NLI Result: intent={self.latest_nli_result.get('intent')}, "
                f"confidence={self.latest_nli_result.get('confidence'):.2f}"
            )
            
            # Try to generate response if we have both NLI and RAG
            self.try_generate_response()
        
        except json.JSONDecodeError as e:
            self.get_logger().error(f"❌ Error parsing NLI JSON: {str(e)}")
        except Exception as e:
            self.get_logger().error(f"❌ Error in NLI callback: {str(e)}")
    
    def rag_callback(self, msg: String):
        """
        Callback for RAG results.
        
        Stores the latest RAG result and triggers inference
        if both NLI and RAG data are available.
        """
        try:
            self.latest_rag_result = json.loads(msg.data)
            
            # Log RAG results summary
            num_results = len(self.latest_rag_result.get('results', []))
            self.get_logger().info(
                f"📥 RAG Result: {num_results} documents retrieved"
            )
            
            # Try to generate response if we have both NLI and RAG
            self.try_generate_response()
        
        except json.JSONDecodeError as e:
            self.get_logger().error(f"❌ Error parsing RAG JSON: {str(e)}")
        except Exception as e:
            self.get_logger().error(f"❌ Error in RAG callback: {str(e)}")
    
    def try_generate_response(self):
        """
        Attempt to generate a response if both NLI and RAG data are available.
        
        This is called by both callbacks and waits until we have:
        - NLI result (intent, entities, confidence)
        - RAG result (retrieved documents with similarity scores)
        
        Then it orchestrates the full inference pipeline.
        """
        
        # Check if we have both required inputs
        if self.latest_nli_result is None:
            self.get_logger().debug("⏳ Waiting for NLI result...")
            return
        
        if self.latest_rag_result is None:
            self.get_logger().debug("⏳ Waiting for RAG result...")
            return
        
        # Both inputs available - proceed with inference
        self.query_count += 1
        self.get_logger().info('=' * 60)
        self.get_logger().info(f'Query #{self.query_count}: Generating response...')
        self.get_logger().info('=' * 60)
        
        try:
            # Extract data from NLI and RAG
            nli_data = self.latest_nli_result
            rag_data = self.latest_rag_result
            
            query = nli_data.get('query', '')
            intent = nli_data.get('intent', 'unknown')
            entities = nli_data.get('entities', {})
            
            # Build context from RAG results
            rag_context = self._build_rag_context(rag_data)
            
            self.get_logger().info(f'Intent: {intent}')
            self.get_logger().info(f'Entities: {entities}')
            self.get_logger().info(f'RAG Context length: {len(rag_context)} characters')
            
            # Build prompt based on intent
            self.get_logger().info(f'Building prompt for intent: {intent}...')
            prompt = self._build_intent_specific_prompt(
                intent=intent,
                query=query,
                entities=entities,
                rag_context=rag_context
            )
            
            if prompt is None:
                self.get_logger().warn(f'No prompt builder for intent: {intent}')
                return
            
            # Generate response using LLM
            if not self.model_loaded:
                self.get_logger().error('❌ Model not loaded - cannot generate response')
                self.failed_responses += 1
                return
            
            self.get_logger().info('🔄 Generating response (this may take 10-30 seconds)...')
            start_time = time.time()
            
            response_text = self.model_loader.generate(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )
            
            inference_time = time.time() - start_time
            self.total_inference_time += inference_time
            
            self.get_logger().info(f'✅ Response generated in {inference_time:.2f}s')
            
            # Build response JSON
            llm_response = {
                'query': query,
                'intent': intent,
                'response': response_text,
                'entities': entities,
                'rag_sources': len(rag_data.get('results', [])),
                'inference_time_seconds': inference_time,
                'model': 'phi-2-q4',
                'query_number': self.query_count
            }
            
            # Publish response
            response_msg = String(data=json.dumps(llm_response))
            self.response_publisher.publish(response_msg)
            
            self.successful_responses += 1
            
            self.get_logger().info('📤 Response published to /llm_response')
            self.get_logger().info('=' * 60)
        
        except Exception as e:
            self.get_logger().error(f'❌ Error generating response: {str(e)}')
            self.failed_responses += 1
            import traceback
            self.get_logger().error(traceback.format_exc())
    
    def _build_rag_context(self, rag_data: Dict) -> str:
        """
        Build a formatted context string from RAG results.
        
        Args:
            rag_data (dict): RAG results containing retrieved documents
        
        Returns:
            str: Formatted context for the prompt
        """
        
        context_parts = []
        results = rag_data.get('results', [])
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            similarity = result.get('similarity_score', 0)
            source = result.get('metadata', {}).get('source', 'unknown')
            
            # Format each result with source and relevance
            part = f"[Source {i}: {source} (Relevance: {similarity:.2%})]\n{content}"
            context_parts.append(part)
        
        if not context_parts:
            return "No specific medical information found. General knowledge may be used."
        
        return "\n\n".join(context_parts)
    
    def _build_intent_specific_prompt(
        self,
        intent: str,
        query: str,
        entities: Dict,
        rag_context: str
    ) -> Optional[str]:
        """
        Build a prompt specific to the detected intent.
        
        Args:
            intent (str): Detected intent from NLI
            query (str): Original patient query
            entities (dict): Extracted entities (medications, conditions, etc.)
            rag_context (str): Retrieved medical information
        
        Returns:
            str or None: Built prompt, or None if intent not recognized
        """
        
        medications = entities.get('medications', [])
        conditions = entities.get('conditions', [])
        patient_name = "Patient"
        
        # Build intent-specific prompts
        if intent == 'ask_medication' and medications:
            medication = medications[0]  # Use first mentioned medication
            return self.prompt_builder.build_medication_info_prompt(
                patient_name=patient_name,
                medication_name=medication,
                rag_context=rag_context
            )
        
        elif intent == 'ask_side_effects' and medications:
            medication = medications[0]
            return self.prompt_builder.build_side_effects_prompt(
                patient_name=patient_name,
                medication_name=medication,
                reported_symptom=query,
                rag_context=rag_context
            )
        
        elif intent == 'health_question':
            conditions_str = ', '.join(conditions) if conditions else None
            return self.prompt_builder.build_health_question_prompt(
                patient_name=patient_name,
                question=query,
                rag_context=rag_context,
                patient_conditions=conditions_str
            )
        
        elif intent == 'emergency_alert':
            conditions_str = ', '.join(conditions) if conditions else 'unknown'
            meds_str = ', '.join(medications) if medications else 'unknown'
            return self.prompt_builder.build_emergency_assessment_prompt(
                patient_name=patient_name,
                symptoms=query,
                patient_conditions=conditions_str,
                medications=meds_str
            )
        
        elif intent == 'medication_reminder' and medications:
            medication = medications[0]
            dosage = ', '.join(entities.get('dosages', ['as prescribed']))
            time_of_day = ', '.join(entities.get('times', ['as scheduled']))
            conditions_str = ', '.join(conditions) if conditions else "health"
            return self.prompt_builder.build_medication_reminder_prompt(
                patient_name=patient_name,
                medication_name=medication,
                dosage=dosage,
                time_of_day=time_of_day,
                purpose=conditions_str,
                rag_context=rag_context
            )
        
        else:
            # Default: use general health question prompt
            return self.prompt_builder.build_health_question_prompt(
                patient_name=patient_name,
                question=query,
                rag_context=rag_context
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return inference statistics."""
        avg_time = (
            self.total_inference_time / self.successful_responses
            if self.successful_responses > 0 else 0
        )
        
        return {
            'total_queries': self.query_count,
            'successful_responses': self.successful_responses,
            'failed_responses': self.failed_responses,
            'success_rate': (
                self.successful_responses / self.query_count
                if self.query_count > 0 else 0
            ),
            'average_inference_time': avg_time,
            'model_loaded': self.model_loaded
        }


def main(args=None):
    """Main entry point for the LLM Inference Node."""
    rclpy.init(args=args)
    llm_node = LLMInferenceNode()
    
    try:
        rclpy.spin(llm_node)
    except KeyboardInterrupt:
        llm_node.get_logger().info('Shutting down LLM Inference Node...')
        stats = llm_node.get_statistics()
        llm_node.get_logger().info(f'Final statistics: {stats}')
    finally:
        llm_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
