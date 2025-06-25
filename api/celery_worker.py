import logging
from celery.exceptions import Ignore
from routes.documents.storage import DocumentStorage
from core.celery import celery_app
from transformers import pipeline
import torch

logger = logging.getLogger("momentum.celery_worker")


@celery_app.task(bind=True)
def generate_summary(self, document_id: str, text: str) -> dict:
    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "document_id": document_id,
                "status": "Loading summarization model...",
            },
        )

        summarizer = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )

        self.update_state(
            state="PROGRESS",
            meta={"document_id": document_id, "status": "Generating summary..."},
        )

        max_chunk = 1024
        if len(text.split()) > max_chunk:
            words = text.split()
            chunks = [
                " ".join(words[i : i + max_chunk])
                for i in range(0, len(words), max_chunk)
            ]

            summaries = []
            for chunk in chunks:
                result = summarizer(
                    chunk, max_length=150, min_length=50, do_sample=False
                )
                summaries.append(result[0]["summary_text"])

            if len(summaries) > 1:
                combined = " ".join(summaries)
                final_result = summarizer(
                    combined, max_length=200, min_length=100, do_sample=False
                )
                summary_text = final_result[0]["summary_text"]
            else:
                summary_text = summaries[0]
        else:
            result = summarizer(text, max_length=150, min_length=50, do_sample=False)
            summary_text = result[0]["summary_text"]

        storage = DocumentStorage()
        storage.store_summary(document_id, summary_text)

        logger.info(f"Summary generated and stored for document {document_id}")

        return {
            "document_id": document_id,
            "summary": summary_text,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Failed to generate summary for {document_id}: {e}")
        self.update_state(
            state="FAILURE", meta={"document_id": document_id, "error": str(e)}
        )
        raise Ignore()
