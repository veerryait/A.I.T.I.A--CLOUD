#!/bin/bash

# A.I.T.I.A - Single Container Startup for Hugging Face Spaces
# This version uses Groq API, so no local Ollama service is needed.

echo "🚀 Starting A.I.T.I.A Engine..."

# 1. Start the FastAPI backend in the background
echo "Starting API server on port 8000..."
PYTHONPATH=. python src/api/server.py &

# 2. Start the Streamlit frontend
# Hugging Face expected port is 7860
echo "Starting Dashboard on port 7860..."
streamlit run dashboards/main.py --server.port=7860 --server.address=0.0.0.0
