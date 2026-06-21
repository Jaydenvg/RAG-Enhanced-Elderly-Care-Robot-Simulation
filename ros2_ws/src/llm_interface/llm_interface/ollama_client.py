"""
Ollama Client for LLM Inference

This module provides a client to interact with Ollama API server.
Ollama runs as a local service and handles all GGUF model loading.

Usage:
    client = OllamaClient(model="phi")
    response = client.generate("What is hypertension?")
"""

import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama LLM API.
    
    Ollama must be running: ollama serve
    Default endpoint: http://localhost:11434
    """
    
    def __init__(self, model: str = "phi", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            model (str): Model name in Ollama (e.g., "phi", "mistral")
            base_url (str): Ollama API endpoint. Default: http://localhost:11434
        """
        self.model = model
        self.base_url = base_url
        self.generate_endpoint = f"{base_url}/api/generate"
        
        logger.info(f"OllamaClient initialized")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  Base URL: {self.base_url}")
        
        # Test connection
        if not self.is_available():
            logger.warning(f"Ollama server not available at {self.base_url}")
            logger.warning(f"Make sure to run: ollama serve")
    
    def is_available(self) -> bool:
        """Check if Ollama server is running and available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt (str): Input prompt
            temperature (float): Sampling temperature (0.0-1.0)
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-K sampling parameter
        
        Returns:
            str: Generated response text
        
        Raises:
            RuntimeError: If Ollama server is unavailable
            requests.RequestException: If API call fails
        
        Example:
            >>> client = OllamaClient(model="phi")
            >>> response = client.generate("What is hypertension?")
            >>> print(response)
        """
        
        if not self.is_available():
            raise RuntimeError(
                f"Ollama server not available at {self.base_url}. "
                f"Run: ollama serve"
            )
        
        try:
            logger.debug(f"Generating with model '{self.model}'")
            
            # Prepare request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "stream": False  # Get full response at once
            }
            
            logger.debug(f"Request payload: {payload}")
            
            # Make request
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=300  # 5-minute timeout for inference
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response: {response.text}")
                raise RuntimeError(error_msg)
            
            # Extract generated text
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text
        
        except requests.RequestException as e:
            error_msg = f"Ollama request failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error during generation: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def generate_with_stats(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate text and return statistics.
        
        Returns:
            dict: Contains 'text', 'generation_time', 'tokens_per_second'
        """
        import time
        
        start_time = time.time()
        generated_text = self.generate(prompt, temperature=temperature)
        elapsed_time = time.time() - start_time
        
        # Rough token estimate
        tokens_generated = len(generated_text) // 4
        
        return {
            'text': generated_text,
            'generation_time': elapsed_time,
            'tokens_per_second': tokens_generated / elapsed_time if elapsed_time > 0 else 0
        }
    
    def list_models(self) -> list:
        """List available models in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing OllamaClient...")
    client = OllamaClient(model="phi")
    
    # Check if Ollama is running
    if not client.is_available():
        print("ERROR: Ollama is not running!")
        print("Start Ollama with: ollama serve")
        exit(1)
    
    # List available models
    models = client.list_models()
    print(f"Available models: {models}")
    
    # Test generation
    test_prompt = "What is hypertension? Answer briefly."
    print(f"\nPrompt: {test_prompt}")
    print("Generating response (this may take 10-30 seconds)...")
    
    try:
        response = client.generate(test_prompt)
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"Error: {e}")

