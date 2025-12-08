from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None
    _vectorstore = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        if self._vectorstore is None:
            try:
                logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL}")
                embedding_model = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self._vectorstore = PineconeVectorStore(
                    index_name=settings.PINECONE_INDEX_NAME,
                    embedding=embedding_model,
                    pinecone_api_key=settings.PINECONE_API_KEY
                )
                logger.info("Vector store initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {e}")
                raise

    async def similarity_search(self, query: str, k: int = 5) -> list:
        if self._vectorstore is None:
            self.initialize()
        try:
            docs = await self._vectorstore.asimilarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def get_retriever(self, k: int = 5):
        if self._vectorstore is None:
            self.initialize()
        return self._vectorstore.as_retriever(search_kwargs={"k": k})

vectorstore_service = VectorStoreService()