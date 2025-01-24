"""
Configuration handler for RAG models, embedding models, and vector databases.
Provides comprehensive configuration management for the RAG system.
"""
from typing import Dict, Any, Optional, List, TypedDict, Literal
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from model_parameters import ModelType, ParameterManager

logger = logging.getLogger(__name__)

class EmbeddingModelConfig(TypedDict):
    """Configuration for embedding models"""
    type: str
    description: str
    vector_size: int

class VectorDBConfig(TypedDict):
    """Configuration for vector databases"""
    type: Literal["Managed", "Local"]
    description: str
    api_key: Optional[str]
    index_name: Optional[str]
    storage_path: Optional[str]

class LLMConfig(TypedDict):
    """Configuration for language models"""
    type: str
    description: str
    max_tokens: int
    temperature: float

class RAGSystemConfig(TypedDict):
    """Configuration for the RAG system"""
    embedding_model: str
    vector_database: str
    vector_search_params: Dict[str, Any]
    llm_model: str
    llm_params: Dict[str, Any]
    logging: Dict[str, Any]

@dataclass
class RAGConfigManager:
    """Manager for RAG system configuration"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the RAG configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.param_manager = ParameterManager()
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files"""
        self.rag_models = self._load_config("rag_models_config.json")
        self.vector_db = self._load_config("vector_db_config.json")
        
        # Initialize system configuration
        self.system_config: RAGSystemConfig = {
            "embedding_model": "text-embedding-ada-002",
            "vector_database": "pinecone",
            "vector_search_params": {"top_k": 5},
            "llm_model": "gpt-4",
            "llm_params": self.param_manager.get_model_parameters(
                "gpt-4", 
                ModelType.CHAT,
                temperature=0.7,
                max_tokens=1500
            ),
            "logging": {"enabled": True, "log_level": "info"}
        }
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_dir / filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config from {filename}: {str(e)}")
            raise
    
    def get_rag_model(self, model_name: str) -> Dict[str, Any]:
        """
        Get RAG model configuration.
        
        Args:
            model_name: Name of the RAG model
            
        Returns:
            RAG model configuration
        """
        if model_name not in self.rag_models["rag_models"]:
            raise ValueError(f"RAG model {model_name} not found")
            
        config = self.rag_models["rag_models"][model_name]
        
        # Special handling for Facebook RAG
        if model_name == "facebook_rag":
            config["vector_db_config"] = self.get_vector_db("facebook_dpr")
            config["index_path"] = os.path.join(
                os.path.dirname(__file__),
                "indexes",
                "facebook_dpr",
                config.get("index_name", "wikipedia_2020")
            )
            
        return config
    
    def get_vector_db(self, db_name: str) -> Dict[str, Any]:
        """
        Get vector database configuration.
        
        Args:
            db_name: Name of the vector database
            
        Returns:
            Vector database configuration
        """
        if db_name not in self.vector_db["vector_databases"]:
            raise ValueError(f"Vector database {db_name} not found")
        return self.vector_db["vector_databases"][db_name]
    
    def get_embedding_model(self, model_name: str) -> Dict[str, Any]:
        """
        Get embedding model configuration.
        
        Args:
            model_name: Name of the embedding model
            
        Returns:
            Embedding model configuration
        """
        models = self.vector_db.get("embedding_models", {})
        if model_name not in models:
            # Return default configuration
            return {
                "type": "OpenAI",
                "description": "Default OpenAI embedding model",
                "vector_size": 1536
            }
        return models[model_name]
    
    def get_llm_config(self, model_name: str) -> Dict[str, Any]:
        """
        Get language model configuration.
        
        Args:
            model_name: Name of the language model
            
        Returns:
            Language model configuration
        """
        models = self.vector_db.get("llm_models", {})
        if model_name not in models:
            # Get default parameters from parameter manager
            return {
                "type": "OpenAI",
                "description": "Default OpenAI language model",
                **self.param_manager.get_model_parameters(
                    model_name,
                    ModelType.CHAT
                )
            }
        return models[model_name]
    
    def get_system_config(self) -> RAGSystemConfig:
        """
        Get current system configuration.
        
        Returns:
            System configuration
        """
        return self.system_config
    
    def update_system_config(self, 
                           embedding_model: Optional[str] = None,
                           vector_database: Optional[str] = None,
                           vector_search_params: Optional[Dict[str, Any]] = None,
                           llm_model: Optional[str] = None,
                           llm_params: Optional[Dict[str, Any]] = None,
                           logging_config: Optional[Dict[str, Any]] = None):
        """
        Update system configuration.
        
        Args:
            embedding_model: New embedding model name
            vector_database: New vector database name
            vector_search_params: New vector search parameters
            llm_model: New language model name
            llm_params: New language model parameters
            logging_config: New logging configuration
        """
        if embedding_model:
            self.system_config["embedding_model"] = embedding_model
        if vector_database:
            self.system_config["vector_database"] = vector_database
        if vector_search_params:
            self.system_config["vector_search_params"].update(vector_search_params)
        if llm_model:
            self.system_config["llm_model"] = llm_model
        if llm_params:
            self.system_config["llm_params"].update(llm_params)
        if logging_config:
            self.system_config["logging"].update(logging_config)
    
    def apply_custom_rule(self, rule_name: str) -> None:
        """
        Apply a custom configuration rule.
        
        Args:
            rule_name: Name of the rule to apply
        """
        rules = self.vector_db.get("custom_rules", {})
        if rule_name not in rules:
            raise ValueError(f"Custom rule {rule_name} not found")
            
        rule = rules[rule_name]
        action = rule.get("action", "")
        
        if "Use text-embedding" in action:
            self.system_config["embedding_model"] = action.split()[-1]
        elif "Use gpt-" in action:
            self.system_config["llm_model"] = action.split()[-1]

# Example usage
if __name__ == "__main__":
    # Initialize configuration manager
    config_manager = RAGConfigManager()
    
    # Get configurations
    rag_model = config_manager.get_rag_model("adaptive_rag")
    vector_db = config_manager.get_vector_db("pinecone")
    embedding_model = config_manager.get_embedding_model("text-embedding-ada-002")
    
    # Update system configuration
    config_manager.update_system_config(
        embedding_model="text-embedding-3-large",
        vector_search_params={"top_k": 10}
    )
    
    # Apply custom rule
    config_manager.apply_custom_rule("when_to_use_4_large")
    
    # Get current system configuration
    system_config = config_manager.get_system_config()
    print("Current system configuration:", system_config)
