"""
Secure key management system for handling API keys.
Supports different key types (Normal API Keys and Service Keys) with appropriate security measures.
"""
from typing import Dict, Any, Optional, Literal
import os
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

KeyType = Literal["normal", "service"]
Environment = Literal["development", "staging", "production"]

class KeyManager:
    """
    Secure key management system for handling different types of API keys.
    Supports encryption, rotation, and access monitoring with environment-specific configurations.
    """
    
    def __init__(self, 
                 config_path: str = "config/keys_config.json",
                 environment: Environment = "development"):
        """
        Initialize the key manager.
        
        Args:
            config_path: Path to the key configuration file
            environment: Current environment (development/staging/production)
        """
        self.config_path = config_path
        self.environment = environment
        self._load_config()
        self._initialize_encryption()
        self._setup_monitoring()
        
    def _load_config(self) -> None:
        """Load key configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading key config: {str(e)}")
            self.config = {"keys": {}}
    
    def _initialize_encryption(self) -> None:
        """Initialize encryption key for secure storage."""
        # Use different encryption keys for different environments
        key = os.getenv(f"KEY_ENCRYPTION_KEY_{self.environment.upper()}")
        if not key:
            key = Fernet.generate_key()
            logger.warning(f"No encryption key found for {self.environment}. Generated new key.")
        
        self.cipher_suite = Fernet(key)
    
    def _setup_monitoring(self) -> None:
        """Setup monitoring based on environment."""
        if self.environment == "production":
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(levelname)s] %(message)s',
                handlers=[
                    logging.FileHandler('logs/key_access.log'),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(level=logging.INFO)
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Get an API key by name with environment-specific handling.
        
        Args:
            key_name: Name of the key to retrieve
            
        Returns:
            The API key if found, None otherwise
        """
        # First try environment variable
        env_key = os.getenv(f"{key_name.upper()}_{self.environment.upper()}")
        if env_key:
            self._log_access(key_name, "environment", self.environment)
            return env_key
            
        # Then try secure storage
        key_config = self.config["keys"].get(key_name)
        if key_config:
            # Check if key is appropriate for environment
            if not self._validate_key_for_environment(key_config):
                logger.warning(f"Key {key_name} not suitable for {self.environment}")
                return None
                
            encrypted_key = self._get_from_secure_storage(key_name)
            if encrypted_key:
                self._log_access(key_name, "secure_storage", self.environment)
                return self._decrypt_key(encrypted_key)
        
        logger.error(f"Key {key_name} not found")
        return None
    
    def store_key(self, 
                  key_name: str, 
                  key_value: str, 
                  key_type: KeyType = "normal",
                  description: str = "",
                  owner: str = "System") -> bool:
        """
        Securely store an API key.
        
        Args:
            key_name: Name for the key
            key_value: The API key to store
            key_type: Type of key (normal/service)
            description: Description of the key's purpose
            owner: Owner or team responsible for the key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate key type for environment
            if not self._validate_key_type_for_environment(key_type):
                logger.error(f"Key type {key_type} not allowed in {self.environment}")
                return False
            
            # Encrypt key
            encrypted_key = self._encrypt_key(key_value)
            
            # Store in secure storage
            self._store_in_secure_storage(key_name, encrypted_key)
            
            # Update config
            self.config["keys"][key_name] = {
                "type": key_type,
                "description": description or f"API key for {key_name}",
                "rotation_period_days": 30 if key_type == "service" else 90,
                "last_rotated": datetime.now().isoformat(),
                "owner": owner,
                "environment": self.environment
            }
            
            self._save_config()
            logger.info(f"Stored {key_type} key {key_name} for {self.environment}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing key {key_name}: {str(e)}")
            return False
    
    def _validate_key_for_environment(self, key_config: Dict[str, Any]) -> bool:
        """Validate if a key is appropriate for the current environment."""
        key_type = key_config.get("type", "normal")
        return self._validate_key_type_for_environment(key_type)
    
    def _validate_key_type_for_environment(self, key_type: KeyType) -> bool:
        """Check if key type is allowed in current environment."""
        if self.environment == "production":
            return key_type == "service"
        elif self.environment == "staging":
            return True  # Allow both types in staging
        else:  # development
            return key_type == "normal"
    
    def rotate_key(self, key_name: str) -> bool:
        """
        Rotate an API key with environment-specific handling.
        
        Args:
            key_name: Name of the key to rotate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key_config = self.config["keys"].get(key_name)
            if not key_config:
                logger.error(f"Key {key_name} not found for rotation")
                return False
            
            # Validate environment
            if not self._validate_key_for_environment(key_config):
                logger.error(f"Cannot rotate key {key_name} in {self.environment}")
                return False
            
            # Here you would implement the actual key rotation logic
            # This might involve calling the API provider's key rotation endpoint
            
            key_config["last_rotated"] = datetime.now().isoformat()
            self._save_config()
            
            logger.info(f"Rotated key {key_name} in {self.environment}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating key {key_name}: {str(e)}")
            return False
    
    def check_rotation_needed(self, key_name: str) -> bool:
        """Check if a key needs rotation based on type and environment."""
        key_config = self.config["keys"].get(key_name)
        if not key_config:
            return False
            
        # Validate environment
        if not self._validate_key_for_environment(key_config):
            return False
            
        last_rotated = datetime.fromisoformat(key_config["last_rotated"])
        rotation_period = timedelta(days=key_config["rotation_period_days"])
        
        return datetime.now() - last_rotated > rotation_period
    
    def _log_access(self, key_name: str, source: str, environment: str) -> None:
        """Log key access with enhanced monitoring for production."""
        if self.environment == "production":
            logger.info(
                f"Key {key_name} accessed from {source} in {environment}",
                extra={
                    "key_name": key_name,
                    "source": source,
                    "environment": environment,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            logger.info(f"Key {key_name} accessed from {source} in {environment}")

    def _encrypt_key(self, key: str) -> bytes:
        """Encrypt an API key."""
        return self.cipher_suite.encrypt(key.encode())

    def _decrypt_key(self, encrypted_key: bytes) -> str:
        """Decrypt an API key."""
        return self.cipher_suite.decrypt(encrypted_key).decode()

    def _store_in_secure_storage(self, key_name: str, encrypted_key: bytes) -> None:
        """Store encrypted key in secure storage."""
        storage_path = Path("secure_storage")
        storage_path.mkdir(exist_ok=True)

        with open(storage_path / f"{key_name}.key", "wb") as f:
            f.write(encrypted_key)

    def _get_from_secure_storage(self, key_name: str) -> Optional[bytes]:
        """Retrieve encrypted key from secure storage."""
        try:
            with open(Path("secure_storage") / f"{key_name}.key", "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def _save_config(self) -> None:
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving key config: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Development environment
    dev_manager = KeyManager(environment="development")
    dev_manager.store_key(
        "openai_api_dev",
        "sk-dev-key",
        "normal",
        "Development API key",
        "Development Team"
    )

    # Production environment
    prod_manager = KeyManager(environment="production")
    prod_manager.store_key(
        "openai_service_prod",
        "sk-prod-key",
        "service",
        "Production service key",
        "Production Team"
    )
