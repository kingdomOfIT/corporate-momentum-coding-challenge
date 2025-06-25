import uuid

from fastapi.testclient import TestClient

DOCUMENTS_URL = "/documents"


def test_get_text_failed_document_not_found(
    client: TestClient,
) -> None:
    # Arrange
    random_document_id = uuid.uuid4()
    url = f"{DOCUMENTS_URL}/{random_document_id}//"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Document with document_id={random_document_id} does not exists"
    }


def test_get_text_successful(client: TestClient) -> None:
    # Arrange
    test_text = "Sample document text"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"document_id": document_id, "text": test_text}
