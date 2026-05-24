import os

from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    DOCUMENTS_DIR = "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = "data/chromadb"

    EMBEDDING_MODEL = "text-embedding-3-small"
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

    LLM_MODEL = "llama3.2"
    LLM_MODEL_LOW = "llama3.2"
