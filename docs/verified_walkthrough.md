# 🦉 A.I.T.I.A: Verified Control Plane Walkthrough

A.I.T.I.A (Autonomous Investigation & Treatment of Infrastructure Anomalies) is now **Fully Verified** and **Cloud-Ready**.

## 🧠 Core Capabilities Verified

We have rigorously tested the system against a matrix of failure scenarios.

### 1. Structural Root Cause Analysis
| Scenario | Symptom | Verified Diagnosis |
| :--- | :--- | :--- |
| **Gateway Latency** | High Latency, Zero Locks | **✅ Ingress Capacity / Upstream Timeout** |
| **DB Deadlock** | High Latency, High Locks | **✅ Transaction Deadlock** |
| **Cache Drift** | High Miss Rate | **✅ Cache Eviction Pressure** |

### 2. The "Intelligence Bridge" (Verified)
The most advanced feature of A.I.T.I.A is its ability to reason about physical symptoms.

> **Scenario**: "Water leaking from rack 4"
> **AI Bridge**: "Interpret as **Hardware Thermal Failure** -> **Coolant Leak** -> **Instruction Throttling** -> **DB Lock Contention**."
> **Result**: **PASSED**. The Architect correctly identified the thermal failure and its cascading effect on the database.

---

## 🚀 Deployment Status

The project is currently in a **Clean Baseline State** (approx 25 vectors) and is ready for:

1.  **Hugging Face Spaces**:
    *   `Requirements`: **CPU Basic** (Free Tier ok due to Groq offloading).
    *   `Persistence`: **Auto-detected** (`/data` volume).
    *   `Secrets`: Requires `GROQ_API_KEY`.

2.  **Local Run**:
    *   `docker-compose up` or `streamlit run app.py`.

## 📂 Key Artifacts
*   **[`app.py`](file:///Users/veerryait11/Documents/Project/causal-control-plane/app.py)**: The unified control plane.
*   **[`groq_client.py`](file:///Users/veerryait11/Documents/Project/causal-control-plane/src/models/groq_client.py)**: The "Bridging Logic" brain.
*   **[`discovery.py`](file:///Users/veerryait11/Documents/Project/causal-control-plane/src/causal/discovery.py)**: The Causal Inference engine (DoWhy).

---

**Mission Accomplished.** The Smart Owl is awake. 🦉✨
