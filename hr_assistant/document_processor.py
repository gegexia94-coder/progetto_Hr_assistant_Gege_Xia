import csv
import hashlib
import json
import os
import tempfile
import uuid
from html.parser import HTMLParser
from zipfile import ZipFile

from config import Config
from semantic_chunking import SemanticChunking


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

    def get_text(self):
        return " ".join(self.parts)


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {
        ".txt": "text",
        ".csv": "data",
        ".json": "data",
        ".xml": "data",
        ".html": "web",
        ".htm": "web",
        ".zip": "archive",
    }

    @staticmethod
    def read_first_lines(file_path, n_lines=100):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return [line.strip() for line, _ in zip(file, range(n_lines))]
        except UnicodeDecodeError:
            return []

    @staticmethod
    def get_file_hash(file_path):
        file_hash = hashlib.md5()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                file_hash.update(chunk)

        return file_hash.hexdigest()

    def get_document_metadata(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        return {
            "hash": self.get_file_hash(file_path),
            "last_modified": os.path.getmtime(file_path),
            "source": os.path.basename(file_path),
            "extension": extension,
            "file_type": self.SUPPORTED_EXTENSIONS.get(extension, "unknown"),
        }

    def convert_to_text(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension in [".txt", ".xml"]:
            return self._read_text(file_path)

        if extension == ".csv":
            return self._read_csv(file_path)

        if extension == ".json":
            return self._read_json(file_path)

        if extension in [".html", ".htm"]:
            return self._read_html(file_path)

        return ""

    def _read_text(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    def _read_csv(self, file_path):
        rows = []

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                rows.append(
                    ", ".join(f"{key}: {value}" for key, value in row.items())
                )

        return "\n".join(rows)

    def _read_json(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _read_html(self, file_path):
        parser = SimpleHTMLTextExtractor()

        with open(file_path, "r", encoding="utf-8") as file:
            parser.feed(file.read())

        return parser.get_text()

    def process_zip_file(self, file_path):
        results = []

        with tempfile.TemporaryDirectory() as temp_dir:
            with ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(temp_dir)

            for root, _, files in os.walk(temp_dir):
                for filename in files:
                    inner_path = os.path.join(root, filename)
                    extension = os.path.splitext(filename)[1].lower()

                    if extension in self.SUPPORTED_EXTENSIONS:
                        content = self.convert_to_text(inner_path)

                        if content.strip():
                            results.append((filename, content))

        return results

    def process_single_document(self, file_path):
        documents = []
        metadatas = []
        ids = []

        extension = os.path.splitext(file_path)[1].lower()
        file_type = self.SUPPORTED_EXTENSIONS.get(extension)

        if not file_type:
            return [], [], []

        if file_type == "archive":
            parts = self.process_zip_file(file_path)
            content = "\n\n".join(
                f"File interno: {filename}\n{text}"
                for filename, text in parts
            )
        else:
            content = self.convert_to_text(file_path)

        if not content.strip():
            return [], [], []

        chunker = SemanticChunking()
        chunks = chunker.chunk_text(content)
        metadata = self.get_document_metadata(file_path)

        for chunk in chunks:
            if chunk.strip():
                documents.append(chunk.strip())
                metadatas.append(metadata)
                ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    def process_documents(self, db):
        current_files = {
            filename: self.get_document_metadata(
                os.path.join(Config.DOCUMENTS_DIR, filename)
            )
            for filename in os.listdir(Config.DOCUMENTS_DIR)
            if os.path.splitext(filename)[1].lower() in self.SUPPORTED_EXTENSIONS
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

                documents, metadatas, ids = self.process_single_document(file_path)

                if documents:
                    db.add_documents(documents, metadatas, ids)

        for filename in files_to_remove:
            db.remove_document_by_source(filename)

        return len(files_to_add), len(files_to_update), len(files_to_remove)
