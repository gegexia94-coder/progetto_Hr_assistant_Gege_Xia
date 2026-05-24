from chromadb.api.types import EmbeddingFunction
from chromadb.utils import embedding_functions

from config import Config


class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        if Config.EMBEDDING_PROVIDER != "openai":
            raise ValueError("In questo progetto usiamo solo embedding OpenAI.")

        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=Config.OPENAI_KEY,
            model_name=Config.EMBEDDING_MODEL,
        )

    def __call__(self, input):
        return self.embedding_function(input)
