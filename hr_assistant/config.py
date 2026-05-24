import os

from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    DOCUMENTS_DIR = "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = "data/chromadb"

    EMBEDDING_MODEL = "text-embedding-3-small"
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

    LLM_MODEL = "gpt-4o-mini"
    LLM_MODEL_LOW = "gpt-4o-mini"
    AI_API_URL = "https://api.openai.com/v1/"
    AI_API_KEY = os.getenv("OPENAI_API_KEY")