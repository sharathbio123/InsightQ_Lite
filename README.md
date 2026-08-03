# InsightQ

InsightQ is a local document assistant built for research workflows. It lets you upload PDFs, build a local vector index, and ask natural language questions against your own documents.

## Project structure
- `backend/` — FastAPI service that exposes `/upload`, `/build`, `/chat`, `/health`, and `/history` endpoints.
- `frontend/` — React SPA with a polished upload/build/chat experience.
- `documents/` — local storage for uploaded PDFs.
- `Test_AI.py` — core RAG pipeline that loads PDFs, splits text, creates embeddings, and connects the retrieval chain to an Ollama-backed LLM.
- `docker-compose.yml` — orchestrates Ollama, the backend, and the frontend for a full Docker deployment.
- `app.py` and the root `Dockerfile` remain as a lightweight Streamlit fallback option, but the React + FastAPI stack is recommended for production use.

## Architecture overview
InsightQ follows a simple local RAG architecture: the browser sends documents and questions to a backend service, the backend builds a retrieval pipeline from the PDFs, and the local LLM answers the question using the retrieved context.

```mermaid
flowchart LR
    U[User in browser] --> F[React frontend]
    F -->|HTTP requests| B[FastAPI backend]
    B -->|save/read PDFs| D[documents/ folder]
    B -->|embedding + chat calls| O[Ollama service]
    O -->|nomic-embed-text| E[Embedding model]
    O -->|llama3.2:3b| L[Chat model]
    B -->|retrieval context| R[Local RAG pipeline]
    R --> L
    L --> F
```

### How the connections work
1. The React frontend sends uploaded PDFs to `POST /upload`.
2. The backend stores the uploaded files in `documents/`.
3. When the user clicks `Build RAG Index`, the backend loads the PDFs, splits them into chunks, generates embeddings with Ollama, and builds a local retrieval chain.
4. When the user asks a question, the frontend sends it to `POST /chat`.
5. The backend retrieves the most relevant document chunks, sends them to the Ollama chat model together with the question, and returns the answer to the frontend.

### Runtime connection map
- Local mode:
  - Frontend: `http://localhost:3000`
  - Backend: `http://localhost:8000`
  - Ollama API: `http://localhost:11434`
- Docker mode:
  - Frontend: `http://localhost:8080`
  - Backend: `http://localhost:8001`
  - Ollama API: `http://localhost:11435`

### Visual architecture diagram
![InsightQ architecture diagram](assets/insightq-architecture.svg)

For a dedicated standalone architecture reference, see [ARCHITECTURE.md](ARCHITECTURE.md).

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
- Ollama API: http://localhost:11435

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
