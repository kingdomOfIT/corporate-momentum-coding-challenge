from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


DOCUMENTS_URL = "/documents"


def test_summarize_text_document_not_found(client: TestClient) -> None:
    # Arrange
    non_existent_id = "non-existent-doc"
    url = f"{DOCUMENTS_URL}/{non_existent_id}/summary"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Document with document_id={non_existent_id} does not exists"
    }


def test_summarize_text_existing_summary_returns_immediately(
    client: TestClient,
) -> None:
    # Arrange
    test_text = "Test document for summarization with existing summary"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    with patch(
        "routes.documents.controller.storage.get_summary",
        return_value="Existing test summary",
    ):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "document_id": document_id,
            "summary": "Existing test summary",
        }


@patch("routes.documents.controller.redis_client")
@patch("routes.documents.controller.generate_summary")
def test_summarize_text_new_task_created(
    mock_generate_summary, mock_redis, client: TestClient
) -> None:
    # Arrange
    test_text = "Test document for new summarization task"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_redis.get.return_value = None

    mock_task = MagicMock()
    mock_task.id = "test-task-id-123"
    mock_generate_summary.delay.return_value = mock_task

    with patch("routes.documents.controller.storage.get_summary", return_value=None):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 202
        expected_response = {
            "document_id": document_id,
            "message": "Summary generation started",
            "task_id": "test-task-id-123",
            "status": "pending",
        }
        assert response.json() == expected_response

        mock_redis.get.assert_called_once_with(f"summary_task:{document_id}")
        mock_redis.setex.assert_called_once_with(
            f"summary_task:{document_id}", 3600, "test-task-id-123"
        )
        mock_generate_summary.delay.assert_called_once_with(document_id, test_text)


@patch("routes.documents.controller.redis_client")
@patch("routes.documents.controller.celery_app")
def test_summarize_text_existing_task_pending(
    mock_celery_app, mock_redis, client: TestClient
) -> None:
    # Arrange
    test_text = "Test document with pending task"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_redis.get.return_value = "existing-task-id"

    mock_task_result = MagicMock()
    mock_task_result.state = "PENDING"
    mock_celery_app.AsyncResult.return_value = mock_task_result

    with patch("routes.documents.controller.storage.get_summary", return_value=None):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 202
        expected_response = {
            "document_id": document_id,
            "message": "Summary is being generated. Please try again soon.",
            "task_id": "existing-task-id",
            "status": "pending",
        }
        assert response.json() == expected_response


@patch("routes.documents.controller.redis_client")
@patch("routes.documents.controller.celery_app")
def test_summarize_text_existing_task_progress(
    mock_celery_app, mock_redis, client: TestClient
) -> None:
    # Arrange
    test_text = "Test document with task in progress"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_redis.get.return_value = "progress-task-id"

    mock_task_result = MagicMock()
    mock_task_result.state = "PROGRESS"
    mock_celery_app.AsyncResult.return_value = mock_task_result

    with patch("routes.documents.controller.storage.get_summary", return_value=None):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 202
        expected_response = {
            "document_id": document_id,
            "message": "Summary is being generated. Please try again soon.",
            "task_id": "progress-task-id",
            "status": "progress",
        }
        assert response.json() == expected_response


@patch("routes.documents.controller.redis_client")
@patch("routes.documents.controller.celery_app")
def test_summarize_text_existing_task_success(
    mock_celery_app, mock_redis, client: TestClient
) -> None:
    # Arrange
    test_text = "Test document with completed task"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_redis.get.return_value = "success-task-id"

    mock_task_result = MagicMock()
    mock_task_result.state = "SUCCESS"
    mock_task_result.result = {
        "document_id": document_id,
        "summary": "Task completed summary",
        "status": "completed",
    }
    mock_celery_app.AsyncResult.return_value = mock_task_result

    with patch("routes.documents.controller.storage.get_summary", return_value=None):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        expected_response = {
            "document_id": document_id,
            "summary": "Task completed summary",
        }
        assert response.json() == expected_response


@patch("routes.documents.controller.redis_client")
@patch("routes.documents.controller.celery_app")
@patch("routes.documents.controller.generate_summary")
def test_summarize_text_existing_task_failed_retry(
    mock_generate_summary, mock_celery_app, mock_redis, client: TestClient
) -> None:
    # Arrange
    test_text = "Test document with failed task"
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_redis.get.return_value = "failed-task-id"

    mock_task_result = MagicMock()
    mock_task_result.state = "FAILURE"
    mock_celery_app.AsyncResult.return_value = mock_task_result

    mock_new_task = MagicMock()
    mock_new_task.id = "retry-task-id-456"
    mock_generate_summary.delay.return_value = mock_new_task

    with patch("routes.documents.controller.storage.get_summary", return_value=None):
        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 202
        expected_response = {
            "document_id": document_id,
            "message": "Summary generation started",
            "task_id": "retry-task-id-456",
            "status": "pending",
        }
        assert response.json() == expected_response

        mock_redis.delete.assert_called_once_with(f"summary_task:{document_id}")

        mock_generate_summary.delay.assert_called_once_with(document_id, test_text)
        mock_redis.setex.assert_called_with(
            f"summary_task:{document_id}", 3600, "retry-task-id-456"
        )


def test_summarize_text_integration_flow(client: TestClient) -> None:
    # Arrange
    test_text = (
        "This is a comprehensive integration test for the summarization API flow."
    )
    store_response = client.post(DOCUMENTS_URL, data={"text": test_text})
    document_id = store_response.json()["document_id"]
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    response1 = client.get(url)

    assert response1.status_code == 202
    response1_data = response1.json()
    assert response1_data["document_id"] == document_id
    assert response1_data["message"] == "Summary generation started"
    assert "task_id" in response1_data
    assert response1_data["status"] == "pending"

    # Act
    response2 = client.get(url)

    # Assert
    assert response2.status_code == 202
    response2_data = response2.json()
    assert response2_data["document_id"] == document_id
    assert "Summary is being generated" in response2_data["message"]


@patch("routes.documents.controller.storage.get_summary")
@patch("routes.documents.controller.get_text")
def test_summarize_text_all_edge_cases(
    mock_get_text, mock_get_summary, client: TestClient
) -> None:
    document_id = "test-doc-id"
    url = f"{DOCUMENTS_URL}/{document_id}/summary"

    mock_get_text.side_effect = FileNotFoundError()
    response = client.get(url)
    assert response.status_code == 404
    assert response.json() == {"message": "Document not found"}

    mock_get_text.side_effect = None
    mock_get_text.return_value = "Test text"

    mock_get_summary.return_value = "Existing summary"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["summary"] == "Existing summary"
