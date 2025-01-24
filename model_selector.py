"""
Model selector module for choosing appropriate OpenAI models based on task requirements.
Integrates with RAG configuration and supports various model selection strategies.
"""

import json
from typing import Optional, Literal, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TaskType = Literal["text_generation", "embedding", "real_time", "audio"]
ContextLength = Literal["short", "long"]
Complexity = Literal["simple", "complex"]

class ModelSelector:
    """
    Handles model selection based on task requirements and configuration.
    Integrates with RAG system configuration for consistent model usage.
    """

    DEFAULT_MODELS = {
        "text_generation": {
            "simple": {
                "short": "gpt-3.5-turbo",
                "long": "gpt-3.5-turbo-16k"
            },
            "complex": {
                "short": "gpt-4",
                "long": "gpt-4-32k"
            }
        },
        "embedding": "text-embedding-ada-002",
        "real_time": "gpt-4-turbo-preview",
        "audio": "whisper-1"
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model selector.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or "config/rag_models_config.json"
        self._load_config()

    def _load_config(self) -> None:
        """Load model configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.warning(f"Error loading config from {self.config_path}: {str(e)}")
            logger.info("Using default model configuration")
            self.config = {}

    def select_model(self, 
                    task_type: TaskType,
                    complexity: Optional[Complexity] = "simple",
                    context_length: Optional[ContextLength] = "short") -> str:
        """
        Select appropriate model based on task requirements.
        
        Args:
            task_type: Type of task (text_generation, embedding, real_time, audio)
            complexity: Task complexity (simple, complex)
            context_length: Expected context length (short, long)
            
        Returns:
            Selected model name
        """
        try:
            # Handle embedding models
            if task_type == "embedding":
                # Check RAG config first
                for rag_model in self.config.get("rag_models", {}).values():
                    if "embedding_model" in rag_model:
                        return rag_model["embedding_model"]
                return self.DEFAULT_MODELS["embedding"]

            # Handle real-time and audio models
            if task_type in ["real_time", "audio"]:
                return self.DEFAULT_MODELS[task_type]

            # Handle text generation models
            if task_type == "text_generation":
                return self.DEFAULT_MODELS["text_generation"][complexity][context_length]

            # Default fallback
            return self.DEFAULT_MODELS["text_generation"]["simple"]["short"]

        except Exception as e:
            logger.error(f"Error selecting model: {str(e)}")
            return self.DEFAULT_MODELS["text_generation"]["simple"]["short"]

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model configuration dictionary
        """
        # First check RAG config
        for rag_model in self.config.get("rag_models", {}).values():
            if rag_model.get("embedding_model") == model_name:
                return rag_model

        # Return default config
        return {
            "max_tokens": 4096 if "16k" in model_name else 2048,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }

    def validate_model(self, model_name: str) -> bool:
        """
        Validate if a model name is supported.
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            True if model is supported, False otherwise
        """
        # Check in default models
        for category in self.DEFAULT_MODELS.values():
            if isinstance(category, dict):
                for subcategory in category.values():
                    if isinstance(subcategory, dict):
                        if model_name in subcategory.values():
                            return True
                    elif subcategory == model_name:
                        return True
            elif category == model_name:
                return True

        # Check in RAG config
        for rag_model in self.config.get("rag_models", {}).values():
            if rag_model.get("embedding_model") == model_name:
                return True

        return False

# Example usage
if __name__ == "__main__":
    selector = ModelSelector()
    
    # Select model for different tasks
    text_model = selector.select_model("text_generation", "complex", "long")
    embedding_model = selector.select_model("embedding")
    realtime_model = selector.select_model("real_time")
    
    print(f"Selected text model: {text_model}")
    print(f"Selected embedding model: {embedding_model}")
    print(f"Selected realtime model: {realtime_model}")
    
    # Get model config
    config = selector.get_model_config(text_model)
    print(f"Model config: {config}")
