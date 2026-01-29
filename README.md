---
title: A.I.T.I.A Cloud Control Plane
emoji: 🦉
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# 🧠 A.I.T.I.A (Cloud Optimized)
### **Autonomous Investigation & Treatment of Infrastructure Anomalies**
#### *A Cloud-Native SRE Agent with Causal Reasoning & Predictive ML*

A.I.T.I.A is a production-ready **Autonomous SRE Agent** designed for the cloud. Unlike traditional monitoring tools that simply flag errors, A.I.T.I.A acts as a "Site Reliability Architect" that uses **Causal Inference**, **Predictive Forecasting**, and **Active Learning** to detect, diagnose, and prescribe fixes for complex infrastructure failures.

---

## 🚀 Key Innovation: The "Intelligence Bridge"
A.I.T.I.A goes beyond software metrics. It features a unique **Bridging Logic** that allows it to reason about physical-to-digital failures.

> **Example**: If you report *"Water leaking from rack 4"*, A.I.T.I.A understands this causes **Hardware Thermal Failure**, leading to **Instruction Throttling** and ultimately **DB Lock Contention**. It will then prescribe `kubectl set resources` to mitigate the throttling.

---

## 🌟 Production-Grade Features (New in v3.0)

### 1. 🔍 Causal Root Cause Analysis (DoWhy)
- Uses statistical **Average Treatment Effect (ATE)** calculations to prove causality.
- Differentiates between symptom (Latency) and root cause (Database Deadlock).
- **Technology**: `DoWhy`, `NetworkX`.

### 2. 🔮 Predictive Analytics (ML Forecasting)
- **Time-Series Forecasting**: Uses a Linear Regression engine to project latency trends 30 minutes into the future.
- **SLO Warning System**: Automatically alerts operators if the *Projected Latency* is expected to breach the 1000ms SLO.
- **Technology**: `Scikit-Learn`, `Pandas`, `Plotly`.

### 3. 🧠 Active Learning Feedback Loop (RLHF)
- **Human-in-the-Loop**: Every diagnosis card features `👍 Correct` / `👎 Incorrect` buttons.
- **Gold Standard Dataset**: User feedback is saved to `data/feedback_dataset.jsonl` to create a verified dataset for future model fine-tuning.

### 4. ☁️ Cloud-Native Architecture
- **Unified Control Plane**: Single-container `app.py` optimized for Hugging Face Spaces.
- **Groq Cloud Brain**: Powered by **Llama-3-70B** via Groq API for architect-level reasoning with zero local footprint.
- **Persistent Memory**: Auto-detects persistent volumes (`/data`) to safeguard vector history.

---

## 🛠️ Quick Start

### Option A: Hugging Face Spaces (Recommended)
1.  Target Hardware: **CPU Basic** (Free Tier).
2.  Set Secret: `GROQ_API_KEY` in settings.
3.  Deploy. The system auto-configures persistence.

### Option B: Local Docker
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/veerryait/A.I.T.I.A--CLOUD.git
    cd A.I.T.I.A--CLOUD
    ```
2.  **Add API Key**
    ```bash
    export GROQ_API_KEY="your_key_here"
    ```
3.  **Run Streamlit App**
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

---

## 🎮 How to Use (The Drill)

### 1. 📥 Ingest Log (Simulation)
Inject distinct failure scenarios to test the agent:
*   **Database Deadlock**: Set `DB Lock Time > 800ms`.
*   **Cache Miss Storm**: Message "Cache miss rate > 80%".
*   **Physical Failure**: Message "Water leaking from rack".

### 2. 🚀 Analyze & Forecast
*   Click **Analyze Now** to trigger the Groq Architect.
*   Check the **"📈 Forecast"** tab to see if your injection will cause a future outage.

### 3. 👍 Teach the AI
*   Use the feedback buttons to rate the diagnosis. This reinforces the "Bridging Logic".

---

## 📂 Project Structure
```text
.
├── app.py                  # Unified Cloud Control Plane
├── src/
│   ├── causal/             # DoWhy Inference Engine
│   ├── models/
│   │   ├── groq_client.py  # The "Architect" Logic (Bridging)
│   │   ├── forecasting.py  # ML Time-Series Engine
│   │   └── memory.py       # ChromaDB Vector Store
├── data/                   # Persistent storage (auto-mounted)
├── Dockerfile.hf           # Cloud-optimized build
└── requirements.txt        # Production dependencies
```

---

## 📜 License
MIT License. Created by [Veerryait](https://github.com/veerryait).

**"Autonomous SRE: Because software should fix itself."** 🦉✨
