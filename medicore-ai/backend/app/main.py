from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.config import settings
from app.api.routes import chat, health
from app.services.vectorstore import vectorstore_service
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MEDICORE AI API",
    description="Medical chatbot with RAG architecture and Google Maps integration",
    version="2.0.0",
)

# CORS Configuration - Use the parser method
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(chat.router, prefix="/chat")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting MEDICORE AI backend...")
    try:
        vectorstore_service.initialize()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.warning(f"Vector store initialization warning: {e}")
        pass

@app.get("/")
async def root():
    return {
        "message": "MEDICORE AI API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Medical chatbot with Groq LLM",
            "RAG with Pinecone vector store",
            "Google Maps hospital finder",
            "Multi-language translation",
            "Medical response formatting"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
