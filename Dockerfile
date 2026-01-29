# Use Python 3.11 as base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvloop streamlit requests streamlit-autorefresh

# Pre-download embedding model (Lightweight: 22MB)
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy project files
COPY src/ ./src/
COPY dashboards/ ./dashboards/
COPY scripts/ ./scripts/

# Ensure necessary directories exist
RUN mkdir -p data/chroma /data/chroma && chmod -R 777 /app/data /data

# Set Environment Variables
ENV PYTHONPATH=/app
ENV API_URL=http://localhost:8000
ENV PERSIST_DATA=true

# Hugging Face Spaces use port 7860
EXPOSE 7860

# Start script
RUN chmod +x scripts/start_hf.sh
CMD ["/app/scripts/start_hf.sh"]
