import hashlib
import os
import uuid

from config import Config
from semantic_chunking import SemanticChunking


class DocumentProcessor:
    @staticmethod
    def read_first_lines(file_path, limit=100):
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        return [line.strip() for line in lines[:limit]]

    @staticmethod
    def get_file_hash(file_path):
        file_hash = hashlib.md5()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                file_hash.update(chunk)

        return file_hash.hexdigest()

    @staticmethod
    def get_document_metadata(file_path):
        return {
            "hash": DocumentProcessor.get_file_hash(file_path),
            "last_modified": os.path.getmtime(file_path),
            "source": os.path.basename(file_path),
        }

    @staticmethod
    def process_single_document(file_path):
        documents = []
        metadatas = []
        ids = []

        metadata = DocumentProcessor.get_document_metadata(file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        chunker = SemanticChunking()
        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            if chunk.strip():
                documents.append(chunk.strip())
                metadatas.append(metadata)
                ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    @staticmethod
    def process_documents(db):
        current_files = {
            filename: DocumentProcessor.get_document_metadata(
                os.path.join(Config.DOCUMENTS_DIR, filename)
            )
            for filename in os.listdir(Config.DOCUMENTS_DIR)
            if filename.endswith(".txt")
        }

        existing_files = db.get_tracked_files()

        files_to_add = set(current_files) - set(existing_files)
        files_to_remove = set(existing_files) - set(current_files)

        files_to_update = {
            filename
            for filename in set(current_files) & set(existing_files)
            if current_files[filename]["hash"] != existing_files[filename]["hash"]
        }

        for action, files in [("add", files_to_add), ("update", files_to_update)]:
            for filename in files:
                file_path = os.path.join(Config.DOCUMENTS_DIR, filename)

                if action == "update":
                    db.remove_document_by_source(filename)

                documents, metadatas, ids = DocumentProcessor.process_single_document(
                    file_path
                )

                if documents:
                    db.add_documents(documents, metadatas, ids)

        for filename in files_to_remove:
            db.remove_document_by_source(filename)

        return len(files_to_add), len(files_to_update), len(files_to_remove)
