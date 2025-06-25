# Momentum Project

A simple REST API service for storing, retrieving, and summarizing large English texts using FastAPI and Celery.

## Features

- **Store Text**: Save large texts and receive a unique `document_id`.
- **Retrieve Text**: Fetch the original text by `document_id`.
- **Summarize Text**: Get a summary of the text by `document_id` (runs in background).

## Tech Stack

- FastAPI (API)
- Celery (background tasks)
- Redis (broker & result backend)
- HuggingFace Transformers (summarization)
- Docker & Docker Compose

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- (Optional) [VS Code Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for faster container rebuilds and development.

### Setup Environment Variables

Before starting, create your `.env` file from the provided example:

```sh
cp api/.env.example api/.env
```

You can edit `api/.env` to adjust any settings if needed.

### Quick Start

1. **Clone the repository:**

   ```sh
   git clone <your-repo-url>
   cd momentum
   ```

2. **Start the services:**

   ```sh
   docker-compose up --build
   ```

   This will start:
   - The FastAPI server on [http://localhost:8000](http://localhost:8000)
   - The Celery worker
   - Redis

3. **(Optional) Use Dev Container:**
   - Open the project in VS Code.
   - Click "Reopen in Container" if prompted, or use the Command Palette: `Dev Containers: Reopen in Container`.
   - This provides a pre-configured environment for faster builds and development.

## API Usage

### 1. Store Text

**Request:**

```sh
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=This is a long text"
```

**Response:**

```json
{
  "document_id": "abc123"
}
```

---

### 2. Retrieve Full Text

**Request:**

```sh
curl http://localhost:8000/documents/abc123
```

**Response:**

```json
{
  "document_id": "abc123",
  "text": "This is a long text ..."
}
```

---

### 3. Retrieve Summary

**Request:**

```sh
curl http://localhost:8000/documents/abc123/summary
```

**Response (if ready):**

```json
{
  "document_id": "abc123",
  "summary": "This is the summary."
}
```

**Response (if still processing):**

```json
{
  "document_id": "abc123",
  "message": "Summary is being generated. Please try again soon.",
  "task_id": "celery-task-id",
  "status": "pending"
}
```

---

## Development Notes

- All data is stored in the `document_storage` folder (created automatically).
- No database is required.
- Summarization is performed using a Celery worker.
- For rapid development and reproducible environments, the project supports VS Code Dev Containers.
