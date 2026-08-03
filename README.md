# InsightQ

InsightQ is a local document assistant built for research workflows. It lets you upload PDFs, build a local vector index, and ask natural language questions against your own documents.

## Project structure
- `backend/` — FastAPI service that wraps the local RAG pipeline and exposes upload, build, and chat APIs.
- `frontend/` — React SPA with a polished upload/build/chat UI.
- `documents/` — local document storage for uploaded PDFs.
- `Test_AI.py` — core RAG pipeline and prompt setup using Ollama embeddings and a local chat model.
- `docker-compose.yml` — orchestrates Ollama, backend, and frontend for a full Docker deployment.
- `app.py` and the root `Dockerfile` remain as a lightweight Streamlit fallback option, but the React + FastAPI stack is recommended for production use.

## Architecture overview
1. Upload PDFs from the browser into `documents/`.
2. The backend builds a local retrieval index and initializes an offline LLM pipeline.
3. Chat queries are answered using the indexed document context and the local model.

## Installation
### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker Engine and Docker Compose (optional for containerized deployment)

### Local Python + React setup
From the repository root:

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

Start the backend:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm start
```

Open `http://localhost:3000` in your browser.

The frontend uses `http://localhost:8000` by default. If your backend runs elsewhere, set:

```bash
REACT_APP_API_BASE=http://<host>:<port> npm start
```

## Docker setup
Use Docker Compose to run the full stack with Ollama, the backend, and the frontend.

```bash
docker compose up --build
```

After startup:
- Frontend: http://localhost:8080
- Backend: http://localhost:8001
- Ollama API: http://localhost:11434

Stop the stack with:

```bash
docker compose down
```

## Usage
1. Upload one or more PDF documents in the InsightQ web UI.
2. Click `Upload PDFs` and then `Build RAG Index`.
3. Ask questions in the chat box.
4. Use the theme toggle and Clear chat button to refresh the workspace.

## Notes
- The active document folder is `documents/`. Store PDFs there or upload from the frontend.
- `documents/*.pdf` is ignored from version control so local data does not get committed.
- Ollama must be available for the RAG pipeline to generate embeddings and chat responses. Pull the required models if needed:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Troubleshooting
- If the backend reports `pipeline not built`, run `Build RAG Index` before asking questions.
- If the frontend cannot reach the backend, check `REACT_APP_API_BASE` or use `docker compose up`.

## Clean GitHub upload
This repository is prepared for GitHub by keeping the core application files and documenting the build/run flow clearly. The `documents/` folder is the active storage path, and local PDF files are excluded from Git history.

=======
