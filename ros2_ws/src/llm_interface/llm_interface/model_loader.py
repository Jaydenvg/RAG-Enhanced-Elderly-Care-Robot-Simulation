"""
LLM Model Loader for Phi-2

This module handles loading and inference with the Phi-2 GGUF model.
Uses llama-cpp-python for efficient local LLM inference on CPU.

Key features:
- Load Phi-2-Q4 GGUF model (quantized for faster inference)
- Generate text with configurable parameters
- Handle model initialization with proper error handling
- Support for streaming and non-streaming responses
"""

import os
import logging
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMModelLoader:
    """
    Handles loading and inference with Phi-2 LLM model.
    
    Attributes:
        model_path (str): Path to the GGUF model file
        model: Loaded llama-cpp model instance
        n_threads (int): Number of CPU threads for inference
        n_ctx (int): Context window size for the model
    """
    
    def __init__(self, model_path: Optional[str] = None, n_threads: int = 4):
        """
        Initialize the LLM Model Loader.
        
        Args:
            model_path (str, optional): Path to Phi-2 GGUF model.
                Default: ./llm_models/phi-2-q4.gguf
            n_threads (int): Number of CPU threads for inference. Default: 4
        
        Raises:
            ImportError: If llama-cpp-python is not installed
            FileNotFoundError: If model file doesn't exist
        """
        
        # Set default model path if not provided
        if model_path is None:
            model_path = os.path.expanduser(
                "~/rag_elderly_care_robot_simulation/llm_models/phi-2-q4.gguf"
            )
        
        self.model_path = model_path
        self.n_threads = n_threads
        self.n_ctx = 2048  # Context window size for Phi-2
        self.model = None
        
        logger.info(f"LLMModelLoader initialized")
        logger.info(f"Model path: {self.model_path}")
        logger.info(f"CPU threads: {self.n_threads}")
    
    def load_model(self) -> bool:
        """
        Load the Phi-2 model from GGUF file.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        
        Raises:
            ImportError: If llama-cpp-python is not installed
            FileNotFoundError: If model file doesn't exist
        """
        
        try:
            # Check if llama-cpp-python is installed
            from llama_cpp import Llama
            logger.info("llama-cpp-python imported successfully")
        except ImportError:
            error_msg = (
                "llama-cpp-python not installed. Install with:\n"
                "pip install llama-cpp-python\n"
                "Or for GPU support:\n"
                "pip install llama-cpp-python[cuda]"
            )
            logger.error(error_msg)
            raise ImportError(error_msg)
        
        # Expand user path and check if file exists
        expanded_path = os.path.expanduser(self.model_path)
        
        if not os.path.exists(expanded_path):
            error_msg = f"Model file not found: {expanded_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Check file size
        file_size_gb = os.path.getsize(expanded_path) / (1024**3)
        logger.info(f"Model file size: {file_size_gb:.2f} GB")
        
        try:
            logger.info(f"Loading Phi-2 model from {expanded_path}...")
            logger.info(f"This may take 30-60 seconds on CPU...")
            
            # Load the GGUF model with optimized settings
            self.model = Llama(
                model_path=expanded_path,
                n_ctx=self.n_ctx,           # Context window
                n_threads=self.n_threads,   # CPU threads
                n_gpu_layers=0,             # CPU-only (set >0 for GPU)
                verbose=False               # Reduce verbosity
            )
            
            logger.info("✅ Phi-2 model loaded successfully!")
            logger.info(f"Model context window: {self.n_ctx} tokens")
            logger.info(f"Using {self.n_threads} CPU threads")
            
            return True
        
        except Exception as e:
            error_msg = f"Error loading model: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise RuntimeError(error_msg)
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        repeat_penalty: float = 1.1
    ) -> str:
        """
        Generate text from a prompt using the Phi-2 model.
        
        Args:
            prompt (str): Input prompt for the model
            max_tokens (int): Maximum tokens to generate. Default: 256
            temperature (float): Sampling temperature (0.0-1.0).
                Lower = more deterministic. Default: 0.7
            top_p (float): Nucleus sampling parameter. Default: 0.95
            top_k (int): Top-K sampling parameter. Default: 40
            repeat_penalty (float): Penalty for repeated tokens. Default: 1.1
        
        Returns:
            str: Generated text response
        
        Raises:
            RuntimeError: If model is not loaded
        
        Example:
            >>> loader = LLMModelLoader()
            >>> loader.load_model()
            >>> response = loader.generate("What is hypertension?")
            >>> print(response)
        """
        
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            logger.debug(f"Generating response for prompt: {prompt[:100]}...")
            
            # Generate response with the model
            output = self.model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=["\n\n", "Patient:", "Doctor:"]  # Stop sequences
            )
            
            # Extract generated text
            generated_text = output['choices'][0]['text'].strip()
            
            logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text
        
        except Exception as e:
            error_msg = f"Error during generation: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def generate_with_stats(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate text and return statistics about the generation.
        
        Returns:
            dict: Contains 'text', 'tokens_generated', 'generation_time'
        """
        
        import time
        
        start_time = time.time()
        generated_text = self.generate(prompt, max_tokens, temperature)
        elapsed_time = time.time() - start_time
        
        # Rough token estimate (1 token ≈ 4 characters)
        tokens_generated = len(generated_text) // 4
        
        return {
            'text': generated_text,
            'tokens_generated': tokens_generated,
            'generation_time': elapsed_time,
            'tokens_per_second': tokens_generated / elapsed_time if elapsed_time > 0 else 0
        }


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing LLMModelLoader...")
    loader = LLMModelLoader()
    
    try:
        print("Loading model (this may take a moment)...")
        loader.load_model()
        
        test_prompt = "What is hypertension?"
        print(f"\nPrompt: {test_prompt}")
        response = loader.generate(test_prompt, max_tokens=100)
        print(f"Response: {response}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
