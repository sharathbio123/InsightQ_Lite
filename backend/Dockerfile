# Production-ready backend image for InsightQ
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies: backend-specific then root requirements
RUN pip install --upgrade pip setuptools wheel
RUN if [ -f backend/requirements.txt ]; then pip install -r backend/requirements.txt; fi
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Expose port
ENV PORT=8000
EXPOSE ${PORT}

# Healthcheck: query the FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Entrypoint
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
