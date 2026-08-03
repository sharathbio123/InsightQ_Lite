FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Install Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt || echo "pip install failed — make sure you have correct package names for langchain integrations"

ENV PORT=8501
EXPOSE ${PORT}

# Streamlit command to run the app
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
