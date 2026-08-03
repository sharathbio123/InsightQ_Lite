Production Dockerfiles (backend + frontend)

This repository now contains production-oriented Dockerfiles for both the backend (FastAPI) and the frontend (React + nginx) for InsightQ. They are designed so you can build independent images and run them behind an orchestrator (docker-compose, Kubernetes, etc.).

Files added:
- backend/Dockerfile
- backend/.dockerignore
- frontend/Dockerfile
- frontend/.dockerignore
- frontend/nginx.conf

Backend notes
- The backend image installs Python dependencies from backend/requirements.txt and root requirements.txt (if present).
- It exposes port 8000 and provides a /health endpoint for container healthchecks.
- Build:
  docker build -f backend/Dockerfile -t insightq-backend:latest .
- Run (example):
  docker run --rm -p 8000:8000 insightq-backend:latest

Frontend notes
- The frontend uses a multi-stage build: Node builds the static files, nginx serves them.
- nginx config proxies /api/ to a service named `backend` (useful with docker-compose). Update proxy_pass if you run the backend on a different host.
- Build:
  docker build -f frontend/Dockerfile -t insightq-frontend:latest .
- Run (example):
  docker run --rm -p 80:80 insightq-frontend:latest

Docker Compose
- A compose file is now included to run the frontend, backend, and Ollama together.
- Start everything with:
  docker compose up --build
- The stack exposes:
  - Frontend: http://localhost
  - Backend: http://localhost:8000
  - Ollama API: http://localhost:11434
- Uploaded PDFs are persisted in the local documents directory.
