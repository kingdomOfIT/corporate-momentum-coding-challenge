from fastapi.testclient import TestClient

DOCUMENTS_URL = "/documents"


def test_store_text_successful(client: TestClient) -> None:
    # Arrange
    test_text = "Test document content"

    # Act
    response = client.post(DOCUMENTS_URL, data={"text": test_text})

    # Assert
    assert response.status_code == 201
    assert "document_id" in response.json()
    assert isinstance(response.json()["document_id"], str)
