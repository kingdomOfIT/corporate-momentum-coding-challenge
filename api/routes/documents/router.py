from fastapi import APIRouter, HTTPException, status, Form
from fastapi.responses import JSONResponse

from . import controller, exceptions

router = APIRouter(prefix="/documents", tags=["Document"])


@router.post("/", operation_id="store_text")
def store_text(
    text: str = Form(...),
) -> JSONResponse:
    return controller.store_text(text=text)


@router.get("/{document_id}", operation_id="get_text", response_model=dict)
def get_text(document_id: str) -> dict:
    try:
        text = controller.get_text(document_id=document_id)
        return {"document_id": document_id, "text": text}
    except exceptions.DocumentDoesNotExistsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{document_id}/summary", operation_id="summarize_text", response_model=dict
)
def summarize_text(document_id: str) -> dict:
    try:
        return controller.summarize_text(document_id=document_id)
    except exceptions.DocumentDoesNotExistsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
