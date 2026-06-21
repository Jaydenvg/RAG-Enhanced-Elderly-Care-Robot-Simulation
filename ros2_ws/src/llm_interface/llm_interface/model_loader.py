"""
LLM Model Loader for Ollama Integration

This module provides a unified interface to load LLM models.
Uses Ollama API for model inference (removes local GGUF dependencies).

Ollama must be running: ollama serve
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMModelLoader:
    """
    Unified LLM loader that uses Ollama API.
    
    This class wraps OllamaClient to provide a compatible interface
    with the rest of the system.
    """
    
    def __init__(self, model_name: str = "phi:latest", base_url: str = "http://localhost:11434"):
        """
        Initialize LLM Model Loader with Ollama backend.
        
        Args:
            model_name (str): Model to use in Ollama. Default: "phi"
            base_url (str): Ollama API endpoint. Default: http://localhost:11434
        """
        from .ollama_client import OllamaClient
        
        self.model_name = model_name
        self.base_url = base_url
        self.client = OllamaClient(model=model_name, base_url=base_url)
        self.model = None  # For compatibility
        
        logger.info(f"LLMModelLoader initialized with Ollama")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Base URL: {self.base_url}")
    
    def load_model(self) -> bool:
        """
        Verify Ollama is running and model is available.
        
        Returns:
            bool: True if ready, False otherwise
        """
        
        if not self.client.is_available():
            logger.error("Ollama server is not available")
            logger.error(f"Start Ollama with: ollama serve")
            return False
        
        # Check if model is available
        available_models = self.client.list_models()
        
        if self.model_name not in available_models:
            logger.warning(f"Model '{self.model_name}' not found in Ollama")
            logger.warning(f"Available models: {available_models}")
            logger.warning(f"Pull the model with: ollama pull {self.model_name}")
            return False
        
        logger.info(f"✅ Ollama ready with model '{self.model_name}'")
        self.model = True  # Set to True to indicate ready
        
        return True
    
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.client.is_available()
    
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
        Generate text using Ollama.
        
        Args:
            prompt (str): Input prompt
            max_tokens (int): Ignored (Ollama manages this)
            temperature (float): Sampling temperature
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-K sampling parameter
            repeat_penalty (float): Ignored (Ollama manages this)
        
        Returns:
            str: Generated response
        """
        
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            response = self.client.generate(
                prompt=prompt,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k
            )
            return response
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise RuntimeError(f"Generation failed: {e}")
    
    def generate_with_stats(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate text and return statistics."""
        return self.client.generate_with_stats(prompt, temperature)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing LLMModelLoader with Ollama...")
    loader = LLMModelLoader(model_name="phi")
    
    if loader.load_model():
        print("Model loaded successfully!")
        
        test_prompt = "What is hypertension?"
        print(f"\nGenerating response for: {test_prompt}")
        response = loader.generate(test_prompt, max_tokens=100)
        print(f"Response: {response}")
    else:
        print("Failed to load model")
