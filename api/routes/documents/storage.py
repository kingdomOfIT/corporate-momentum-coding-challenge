import uuid
from pathlib import Path


class DocumentStorage:
    def __init__(self, base_path: str = "document_storage"):
        self.base_path = Path(base_path).absolute()
        self.base_path.mkdir(exist_ok=True)

    def store_document(self, text: str) -> str:
        document_id = str(uuid.uuid4())
        file_path = self.base_path / f"{document_id}.txt"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            raise

        return document_id

    def get_document(self, document_id: str) -> str:
        file_path = self.base_path / f"{document_id}.txt"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error retrieving document {document_id}: {str(e)}")
            raise

    def get_summary(self, document_id: str) -> str | None:
        summary_path = self.base_path / f"{document_id}-summary.txt"

        if not summary_path.exists():
            return None

        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error retrieving summary for document {document_id}: {str(e)}")
            raise

    def store_summary(self, document_id: str, summary: str):
        summary_path = self.base_path / f"{document_id}-summary.txt"

        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
        except Exception as e:
            print(f"Error storing summary for document {document_id}: {str(e)}")
            raise
