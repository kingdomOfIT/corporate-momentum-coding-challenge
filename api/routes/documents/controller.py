from .storage import DocumentStorage
from .exceptions import DocumentDoesNotExistsError
from fastapi.responses import JSONResponse
from fastapi import status
from celery_worker import generate_summary
from core.celery import celery_app, redis_client

storage = DocumentStorage()


def get_text(document_id: str) -> dict:
    text = storage.get_document(document_id)
    if not text:
        raise DocumentDoesNotExistsError(
            attribute_name="document_id", attribute_value=document_id
        )

    return text


def store_text(text: str) -> str:
    document_id = storage.store_document(text)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content={"document_id": document_id}
    )


def summarize_text(document_id: str) -> JSONResponse:
    try:
        text = get_text(document_id)
    except FileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Document not found"},
        )

    existing_summary = storage.get_summary(document_id)
    if existing_summary:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"document_id": document_id, "summary": existing_summary},
        )

    task_key = f"summary_task:{document_id}"
    existing_task_id = redis_client.get(task_key)

    if existing_task_id:
        task_result = celery_app.AsyncResult(existing_task_id)

        if task_result.state in ["PENDING", "PROGRESS"]:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "document_id": document_id,
                    "message": "Summary is being generated. Please try again soon.",
                    "task_id": existing_task_id,
                    "status": task_result.state.lower(),
                },
            )
        elif task_result.state == "SUCCESS":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "document_id": document_id,
                    "summary": task_result.result["summary"],
                },
            )
        else:
            redis_client.delete(task_key)

    task = generate_summary.delay(document_id, text)

    redis_client.setex(task_key, 3600, task.id)

    print(f"Started summary task {task.id} for document {document_id}")

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "document_id": document_id,
            "message": "Summary generation started",
            "task_id": task.id,
            "status": "pending",
        },
    )
