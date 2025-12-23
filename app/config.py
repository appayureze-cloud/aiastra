"""
Configuration settings for the FastAPI application
"""

import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Model configuration
    BASE_MODEL: str = os.getenv("BASE_MODEL", "unsloth/llama-3.1-8b-bnb-4bit")
    LORA_MODEL: str = os.getenv("LORA_MODEL", "ayureasehealthcare/llama3-ayurveda-lora-v3")
    
    # Device configuration
    DEVICE: str = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "auto"
    
    # Model parameters
    MAX_LENGTH: int = int(os.getenv("MAX_LENGTH", "2048"))
    LOAD_IN_4BIT: bool = os.getenv("LOAD_IN_4BIT", "true").lower() == "true"
    LOAD_IN_8BIT: bool = os.getenv("LOAD_IN_8BIT", "false").lower() == "true"
    
    # API configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "7860"))
    
    # Hugging Face token (if required for private models)
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    # Generation defaults
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 0.9
    DEFAULT_TOP_K: int = 50
    DEFAULT_MAX_LENGTH: int = 512

# Global settings instance
settings = Settings()
