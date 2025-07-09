import os
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./insightbot.db")
    
    # Application Configuration
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # File Upload Configuration
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # FAISS Configuration
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Evaluation Configuration
    evaluation_model: str = os.getenv("EVALUATION_MODEL", "gpt-4o-mini")
    evaluation_threshold: float = float(os.getenv("EVALUATION_THRESHOLD", "3.0"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "./logs/insightbot.log")
    
    class Config:
        env_file = ".env"


settings = Settings()