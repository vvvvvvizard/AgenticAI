"""
Comprehensive parameter management for OpenAI models including GPT, DALL-E, and Whisper.
Provides type-safe parameter handling, validation, and model-specific configurations.
"""

from typing import Dict, Any, Optional, List, Union, TypedDict, Literal
from dataclasses import dataclass, field
import logging
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Enum for different types of OpenAI models"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    AUDIO = "audio"
    IMAGE = "image"

class BaseParameters(TypedDict, total=False):
    """Base parameters common to most models"""
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop: Optional[Union[str, List[str]]]
    n: int
    stream: bool
    logprobs: Optional[int]
    echo: bool
    logit_bias: Dict[str, float]
    user: str

class WhisperParameters(TypedDict, total=False):
    """Parameters specific to Whisper model"""
    language: str
    audio_path: str

class DallEParameters(TypedDict, total=False):
    """Parameters specific to DALL-E model"""
    size: Literal["256x256", "512x512", "1024x1024"]
    n: int

@dataclass
class ModelConfig:
    """Configuration class for model parameters with validation"""
    
    # Load parameter definitions and defaults
    CONFIG_PATH = "config/model_parameters_config.json"
    
    def __init__(self):
        """Initialize with configuration from file"""
        self.load_config()
    
    def load_config(self):
        """Load parameter definitions and defaults from config file"""
        try:
            with open(self.CONFIG_PATH, 'r') as f:
                config = json.load(f)
                self.parameter_definitions = config["parameter_definitions"]
                self.model_specific_parameters = config["model_specific_parameters"]
                self.model_defaults = config["model_defaults"]
        except Exception as e:
            logger.error(f"Error loading parameter config: {str(e)}")
            raise

class ParameterManager:
    """Manages parameters for different model types with validation"""
    
    def __init__(self):
        """Initialize with model configuration"""
        self.config = ModelConfig()
    
    def get_parameter_info(self, param_name: str) -> Dict[str, Any]:
        """Get information about a parameter"""
        return self.config.parameter_definitions.get(param_name, {})
    
    def validate_parameter(self, param_name: str, value: Any) -> bool:
        """Validate a parameter value against its definition"""
        param_info = self.get_parameter_info(param_name)
        
        if not param_info:
            return True  # Unknown parameter, assume valid
            
        if "range" in param_info:
            min_val, max_val = param_info["range"]
            if not min_val <= value <= max_val:
                logger.warning(
                    f"Parameter {param_name} value {value} outside range "
                    f"[{min_val}, {max_val}]"
                )
                return False
                
        if "allowed_values" in param_info and value not in param_info["allowed_values"]:
            logger.warning(
                f"Parameter {param_name} value {value} not in allowed values: "
                f"{param_info['allowed_values']}"
            )
            return False
            
        return True
    
    def get_model_parameters(self, 
                           model: str, 
                           model_type: ModelType,
                           **kwargs) -> Dict[str, Any]:
        """
        Get validated parameters for a specific model.
        
        Args:
            model: Name of the model
            model_type: Type of model
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of validated parameters
        """
        # Start with model defaults
        params = self.config.model_defaults.get(model, {}).copy()
        
        # Add provided parameters
        for param, value in kwargs.items():
            if self.validate_parameter(param, value):
                params[param] = value
        
        # Add model-specific handling
        if model_type == ModelType.AUDIO:
            self._handle_audio_parameters(params, kwargs)
        elif model_type == ModelType.IMAGE:
            self._handle_image_parameters(params, kwargs)
        
        return params
    
    def _handle_audio_parameters(self, params: Dict[str, Any], kwargs: Dict[str, Any]):
        """Handle Whisper-specific parameters"""
        if "audio_path" in kwargs:
            params["audio"] = kwargs["audio_path"]
        if "language" in kwargs:
            params["language"] = kwargs["language"]
    
    def _handle_image_parameters(self, params: Dict[str, Any], kwargs: Dict[str, Any]):
        """Handle DALL-E specific parameters"""
        if "size" in kwargs:
            size = kwargs["size"]
            if size in ["256x256", "512x512", "1024x1024"]:
                params["size"] = size
        if "n" in kwargs:
            params["n"] = min(kwargs["n"], 10)  # DALL-E limit

class ParameterPresets:
    """Predefined parameter presets for common use cases"""
    
    def __init__(self):
        self.manager = ParameterManager()
    
    def creative(self, model: str = "gpt-4") -> Dict[str, Any]:
        """Parameters for creative text generation"""
        return self.manager.get_model_parameters(
            model,
            ModelType.CHAT,
            temperature=0.9,
            top_p=0.9,
            frequency_penalty=0.6,
            presence_penalty=0.6
        )
    
    def precise(self, model: str = "gpt-4") -> Dict[str, Any]:
        """Parameters for precise, deterministic responses"""
        return self.manager.get_model_parameters(
            model,
            ModelType.CHAT,
            temperature=0.2,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
    
    def balanced(self, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """Balanced parameters for general use"""
        return self.manager.get_model_parameters(
            model,
            ModelType.CHAT,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
    
    def streaming(self, model: str = "gpt-4") -> Dict[str, Any]:
        """Parameters optimized for streaming responses"""
        return self.manager.get_model_parameters(
            model,
            ModelType.CHAT,
            temperature=0.7,
            stream=True,
            presence_penalty=0.3
        )
    
    def transcription(self, language: str = "en") -> Dict[str, Any]:
        """Parameters for audio transcription"""
        return self.manager.get_model_parameters(
            "whisper-1",
            ModelType.AUDIO,
            language=language
        )
    
    def image_generation(self, 
                        size: str = "1024x1024", 
                        n: int = 1) -> Dict[str, Any]:
        """Parameters for image generation"""
        return self.manager.get_model_parameters(
            "dall-e-2",
            ModelType.IMAGE,
            size=size,
            n=n
        )

# Example usage
if __name__ == "__main__":
    # Initialize parameter manager
    param_manager = ParameterManager()
    presets = ParameterPresets()
    
    # Get creative chat parameters
    creative_params = presets.creative()
    print("Creative parameters:", creative_params)
    
    # Get audio transcription parameters
    audio_params = presets.transcription(language="en")
    print("Audio parameters:", audio_params)
    
    # Get image generation parameters
    image_params = presets.image_generation(size="1024x1024", n=2)
    print("Image parameters:", image_params)
    
    # Custom parameters with validation
    custom_params = param_manager.get_model_parameters(
        "gpt-4",
        ModelType.CHAT,
        temperature=0.8,
        max_tokens=2000,
        frequency_penalty=0.5
    )
    print("Custom parameters:", custom_params)
