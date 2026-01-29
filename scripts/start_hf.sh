#!/bin/bash

# A.I.T.I.A - Single Container Startup for Hugging Face Spaces
# Unified Control Plane (v3.0)

echo "🚀 Starting A.I.T.I.A Unified Control Plane..."

# Start the Streamlit frontend (Unified App) directly
# Hugging Face expected port is 7860
echo "Starting App on port 7860..."
streamlit run app.py --server.port=7860 --server.address=0.0.0.0
