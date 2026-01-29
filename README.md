# 🧠 A.I.T.I.A
### **Autonomous Investigation & Treatment of Infrastructure Anomalies**

A.I.T.I.A is a cutting-edge, **local-first** autonomous SRE (Site Reliability Engineering) agent. It uses **Causal Inference** and **Local LLMs** to detect, diagnose, and suggest remediations for microservice failures in real-time—all with **zero cloud cost** and total data privacy.

---

## 🚀 Key Features
- **Causal Discovery**: Automatically builds a graph of service dependencies and identifies the root cause using the PC algorithm.
- **Local AI Brain**: Powered by `phi3:mini` running via Ollama for private, high-speed diagnostics.
- **Semantic Log Memory**: Uses ChromaDB to store and retrieve similar past incidents for faster resolution.
- **Service Discovery**: Real-time monitoring of API Gateways, User Services, Payment DBs, and Redis Caches.
- **Instant Remediation**: Recommends technical actions (e.g., `restart_service`, `increase_pool`, `flush_cache`) based on dynamic causal chains.

---

## 🏗️ Tech Stack
- **AI/ML**: Ollama (`phi3:mini`), Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Causal Engine**: DoWhy, NetworkX
- **Backend**: FastAPI, Uvicorn, UVLoop
- **Frontend**: Streamlit (with real-time auto-refresh)
- **Database**: ChromaDB (Vector Store)
- **Ops**: Docker, Docker Compose

---

## 🛠️ Installation

### Prerequisites
1.  **Docker & Docker Compose**: [Install here](https://www.docker.com/products/docker-desktop/)
2.  **Ollama**: [Install here](https://ollama.com/) (Required for local LLM inference)

### Setup Steps
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/veerryait/A.I.T.I.A.git
    cd A.I.T.I.A
    ```

2.  **Pull the AI Model**
    Open your terminal and run:
    ```bash
    ollama pull phi3:mini
    ```

3.  **Start the Factory**
    ```bash
    docker-compose -f infra/docker-compose.yml up --build -d
    ```

---

## 🎮 How to Use

1.  **Open the Dashboard**
    Navigate to `http://localhost:8501` in your browser.

2.  **Scenario Training (The Drill)**
    Check out the [Verification Guide](verification_guide.md) (or see internal artifacts) for specific scenarios like "Database Deadlocks" or "Connection Pool Exhaustion."

3.  **Investigate**
    - Use the **Ingest Log** form to simulate errors.
    - Watch the **Recent AI Actions** cards appear as the "Smart Owl" analyzes the logs.
    - Use the **Search logs** box for semantic search over historical failures.

4.  **Maintenance**
    - **Clear AI Cards**: Cleans your dashboard UI.
    - **Wipe All Memory**: Completely resets the vector database and stats for a fresh start.

---

## 🧠 How it Works: The Inner Brain

### 1. The Ingestion Loop
Logs arrive at the FastAPI server and are immediately embedded using a tiny (22MB) but powerful Transformer model. These are stored in ChromaDB.

### 2. The Causal Engine
When errors cross a threshold, the system triggers a **Causal Discovery** pass. It uses structural causal models to determine if an error in a "Payment DB" is the true root cause or just a symptom of a "User Service" lag.

### 3. The LLM Diagnostician
The controller passes the causal graph + the raw error logs to **Phi-3**. Because the AI has "Local Memory" and "Causal Logic," it doesn't just guess—it reasons about the infrastructure.

---

## 📂 Project Structure
```text
.
├── dashboards/         # Streamlit UI
├── infra/              # Docker Compose & orchestrator configs
├── src/
│   ├── agents/         # Async Controller & Orchestrator
│   ├── api/            # FastAPI Server
│   ├── causal/         # DoWhy & NetworkX logic
│   ├── models/         # LLM Client & ChromaDB Memory
│   └── ingestion/      # Synthetic log generators
└── tests/              # End-to-end smoke tests
```

---

## 📜 License
MIT License. Created by [Veerryait](https://github.com/veerryait).

**May your latencies stay low and your cache hits stay high!** 🚀🦉✨
