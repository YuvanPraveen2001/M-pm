"""
Model Configuration for Healthcare Chatbot
Defines the embedding and chat models to use with Ollama
"""

import os
from typing import Optional

# Ollama Model Configuration
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "phi3:mini"

# Ollama server configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model settings
EMBEDDING_DIMENSION = 768  # nomic-embed-text embedding dimension
MAX_TOKENS = 2048
TEMPERATURE = 0.1  # Low temperature for more consistent SQL generation

# Fallback models if primary ones aren't available
FALLBACK_EMBED_MODEL = "all-MiniLM-L6-v2"  # SentenceTransformer fallback
FALLBACK_CHAT_MODEL = "phi3:mini"

def get_embedding_model_config() -> dict:
    """Get embedding model configuration"""
    return {
        "model": EMBED_MODEL,
        "host": OLLAMA_HOST,
        "dimension": EMBEDDING_DIMENSION
    }

def get_chat_model_config() -> dict:
    """Get chat model configuration"""
    return {
        "model": CHAT_MODEL,
        "host": OLLAMA_HOST,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE
    }

def get_available_models() -> dict:
    """Get all available model configurations"""
    return {
        "embedding": get_embedding_model_config(),
        "chat": get_chat_model_config(),
        "fallback_embedding": FALLBACK_EMBED_MODEL,
        "fallback_chat": FALLBACK_CHAT_MODEL
    }
