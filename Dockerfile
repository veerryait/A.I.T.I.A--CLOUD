# Use Python 3.11 slim as base
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

# Pre-download embedding model
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy project files
COPY src/ ./src/
COPY dashboards/ ./dashboards/
COPY data/ ./data/

# Set Python path
ENV PYTHONPATH=/app

# Expose ports for API and Streamlit
EXPOSE 8000 8501

# Default command (overridden by docker-compose for specific services)
CMD ["python", "src/api/server.py"]
