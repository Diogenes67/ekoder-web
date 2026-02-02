"""
EKoder Web Configuration
Loads settings from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class Settings:
    # HuggingFace API
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_API_URL: str = "https://router.huggingface.co/novita/v3/openai/chat/completions"
    HF_MODEL: str = "meta-llama/llama-3.3-70b-instruct"

    # Ollama for embeddings
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    EMBED_MODEL: str = "mxbai-embed-large"

    # CORS
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Security (Phase 3)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Retrieval settings
    TOP_K_TFIDF: int = 35
    TOP_K_EMBED: int = 35
    TOP_K_FINAL: int = 50

    # Data paths
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    ED_CODES_FILE: Path = DATA_DIR / "ed_short_list.json"
    EMBEDDINGS_CACHE: Path = DATA_DIR / "embeddings_mxbai_cache.npy"

settings = Settings()

# Validate at startup, not import time (for Railway deployment)
def validate_settings():
    if not settings.HF_TOKEN:
        raise ValueError("HF_TOKEN environment variable is required")
