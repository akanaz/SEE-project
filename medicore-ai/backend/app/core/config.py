from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    GROQ_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TOP_K: int = 5
    DATABASE_URL: str = "sqlite:///./test.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
