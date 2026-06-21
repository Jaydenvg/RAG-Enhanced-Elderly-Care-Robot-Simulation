"""
LLM Interface Package - Phi-2 Model Integration for Elderly Care Robot

This package provides LLM-based response generation for the elderly care robot.

Main components:
- ModelLoader: Loads and manages Phi-2 GGUF model inference
- PromptBuilder: Constructs context-aware prompts for different scenarios
- LLMInferenceNode: ROS2 node that orchestrates NLI → RAG → LLM pipeline

Usage:
    from llm_interface import ModelLoader, PromptBuilder, LLMInferenceNode
    
    # Load model
    loader = ModelLoader()
    loader.load_model()
    
    # Generate response
    response = loader.generate("What is hypertension?")
"""

from .model_loader import LLMModelLoader
from .prompt_builder import PromptBuilder
from .llm_node import LLMInferenceNode, main

__all__ = [
    'LLMModelLoader',
    'PromptBuilder',
    'LLMInferenceNode',
    'main'
]

__version__ = '0.1.0'
