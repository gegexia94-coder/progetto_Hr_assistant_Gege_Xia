import chromadb

from config import Config
from custom_embedding import CustomEmbeddingFunction


class Database:
    def __init__(self):
        self.embedding_function = CustomEmbeddingFunction()

        self.client = chromadb.PersistentClient(
            path=Config.PERSISTENT_DIR
        )

        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def add_documents(self, documents, metadatas, ids):
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(self, query_text, n_results=1):
        return self.collection.query(query_texts=[query_text], n_results=n_results)

    def get_tracked_files(self):
        result = self.collection.get()
        metadatas = result.get("metadatas") or []

        tracked_files = {}

        for metadata in metadatas:
            source = metadata.get("source")

            if source and source not in tracked_files:
                tracked_files[source] = {
                    "hash": metadata.get("hash"),
                    "last_modified": metadata.get("last_modified"),
                    "source": source,
                }

        return tracked_files

    def remove_document_by_source(self, source):
        result = self.collection.get(where={"source": source})
        ids = result.get("ids") or []

        if ids:
            self.collection.delete(ids=ids)

    def clear(self):
        result = self.collection.get()
        ids = result.get("ids") or []

        if ids:
            self.collection.delete(ids=ids)

    def stats(self):
        result = self.collection.get()
        ids = result.get("ids") or []
        metadatas = result.get("metadatas") or []
        sources = {item.get("source") for item in metadatas if item}

        return {
            "chunks": len(ids),
            "files": len(sources),
            "sources": sorted(sources),
        }
