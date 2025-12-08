import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextbookIngestion:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "medicore-medical-index")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "abhinand/MedEmbed-small-v1")
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.pc = Pinecone(api_key=self.pinecone_api_key)

    def create_index_if_not_exists(self):
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            logger.info(f"Creating index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=384,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            logger.info("Index created successfully")
        else:
            logger.info(f"Index {self.index_name} already exists")

    def process_textbook(self, pdf_path: str):
        logger.info(f"Processing: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "source": os.path.basename(pdf_path),
                "chunk_id": i,
                "type": "medical_textbook"
            })
        return chunks

    def ingest_to_pinecone(self, chunks: list):
        logger.info(f"Uploading {len(chunks)} chunks to Pinecone...")
        vectorstore = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=self.index_name,
            pinecone_api_key=self.pinecone_api_key
        )
        logger.info("Upload complete!")
        return vectorstore

    def ingest_directory(self, textbooks_dir: str):
        textbooks_path = Path(textbooks_dir)
        pdf_files = list(textbooks_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {textbooks_dir}")
            return
        logger.info(f"Found {len(pdf_files)} PDF files")
        self.create_index_if_not_exists()
        all_chunks = []
        for pdf_file in pdf_files:
            try:
                chunks = self.process_textbook(str(pdf_file))
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
        if all_chunks:
            self.ingest_to_pinecone(all_chunks)
            logger.info(f"Successfully ingested {len(all_chunks)} total chunks")
        else:
            logger.warning("No chunks to ingest")

def main():
    textbooks_dir = Path(__file__).parent.parent.parent / "textbooks"
    if not textbooks_dir.exists():
        logger.error(f"Textbooks directory not found: {textbooks_dir}")
        logger.info("Please create 'textbooks/' directory and add PDF files")
        return
    ingestion = TextbookIngestion()
    ingestion.ingest_directory(str(textbooks_dir))

if __name__ == "__main__":
    main()