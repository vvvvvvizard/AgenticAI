"""
Preprocessing module for text cleaning, parameter validation, and embedding preparation.
"""
from typing import Dict, Any, Union, List
import re
import unicodedata

def clean_text(text: str) -> str:
    """
    Remove unnecessary characters and normalize text formatting.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with normalized spacing and formatting
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace multiple spaces and newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()

def clean_query(query: str) -> str:
    """
    Clean and normalize search queries.
    
    Args:
        query: Input search query
        
    Returns:
        Cleaned and normalized query
    """
    # Remove special characters that might affect search
    query = re.sub(r'[^\w\s]', ' ', query.lower())
    
    # Remove extra whitespace
    query = ' '.join(query.split())
    
    return query.strip()

def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean parameters for tool calls.
    
    Args:
        params: Dictionary of parameters to validate
        
    Returns:
        Validated and cleaned parameters
    """
    cleaned_params = {}
    
    for key, value in params.items():
        # Convert string numbers to actual numbers
        if isinstance(value, str) and value.isdigit():
            cleaned_params[key] = int(value)
        # Clean text parameters
        elif isinstance(value, str):
            cleaned_params[key] = clean_text(value)
        # Handle nested dictionaries
        elif isinstance(value, dict):
            cleaned_params[key] = validate_parameters(value)
        # Handle lists
        elif isinstance(value, list):
            cleaned_params[key] = [
                validate_parameters(item) if isinstance(item, dict)
                else clean_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            cleaned_params[key] = value
            
    return cleaned_params

def filter_data(data: Union[List, Dict], min_length: int = 10) -> Union[List, Dict]:
    """
    Filter data based on content quality and relevance.
    
    Args:
        data: Input data to filter
        min_length: Minimum length for text content
        
    Returns:
        Filtered data meeting quality criteria
    """
    if isinstance(data, list):
        return [
            item for item in data
            if isinstance(item, str) and len(clean_text(item)) >= min_length
        ]
    elif isinstance(data, dict):
        return {
            key: value for key, value in data.items()
            if isinstance(value, str) and len(clean_text(value)) >= min_length
        }
    return data

def preprocess_for_embedding(text: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Preprocess text data specifically for embedding models.
    
    Args:
        text: Input text or list of texts to preprocess
        
    Returns:
        Preprocessed text ready for embedding
    """
    if isinstance(text, list):
        return [preprocess_single_text(t) for t in text]
    return preprocess_single_text(text)

def preprocess_single_text(text: str) -> str:
    """
    Preprocess a single text for embedding.
    
    Args:
        text: Single text string to preprocess
        
    Returns:
        Preprocessed text ready for embedding
    """
    # Clean the text
    text = clean_text(text)
    
    # Convert to lowercase for consistency
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove numbers but keep important ones in context
    text = re.sub(r'\b\d+\b(?!\s*(?:year|month|day|dollar|percent|%)s?\b)', '', text)
    
    # Normalize whitespace again
    text = ' '.join(text.split())
    
    return text.strip()
