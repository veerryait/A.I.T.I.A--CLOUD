# 🧪 Comprehensive A.I.T.I.A Verification Guide

This guide provides a rigorous testing matrix to verify **every** service, latency level, and causal parameter in the A.I.T.I.A Control Plane.

## 📋 Test Matrix Overview

We will test the 4 core services against 4 distinct failure scenarios to validate the **Causal Engine** and **Groq Architect**.

| Test ID | Service | Scenario | Key Parameters (ms) | Expected Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | `api-gateway` | **High Latency / Traffic Spike** | Lat: 4500, Lock: 0, Pool: 0 | **Ingress Congestion** / Upstream Timeout |
| **T-02** | `payment-db` | **Deadlock / Contention** | Lat: 3000, Lock: 1000, Pool: 500 | **Database Row Locking** / Contention |
| **T-03** | `redis-cache` | **Cache Miss Storm** | Lat: 1500, Lock: 0, Pool: 0 | **Cache Eviction Pressure** / Miss Rate |
| **T-04** | `user-service`| **Connection Pool Starvation**| Lat: 2500, Lock: 100, Pool: 800 | **Connection Pool Exhaustion** |

---

## 🛠️ Execution Steps

For each test, follow this **exact** sequence:
1.  **Inject**: Fill the "Ingest Log" form with the values specified.
2.  **Repeat**: Click "Inject Signal" **3 times** to establish a pattern.
3.  **Analyze**: Click **🚀 Analyze Now**.
4.  **Verify**: Check the **Glow Card** result and the **Causal Graph** edges.

---

## 🔬 Detailed Test Cases

### 🔵 Test T-01: API Gateway Saturation
*Verify that pure latency without locks is identified as a capacity issue.*

*   **Service**: `api-gateway`
*   **Latency**: `4500` ms
*   **Level**: `ERROR`
*   **Message**: `Gateway timeout - upstream unavailable`
*   **DB Lock Time**: `0` ms
*   **Pool Wait Time**: `0` ms
*   **Expected Root Cause**: `Ingress Capacity Reached` or `Upstream Timeout`

### 🟠 Test T-02: Payment DB Deadlock
*Verify the "Bridging Logic" detects locks causing latency.*

*   **Service**: `payment-db`
*   **Latency**: `3500` ms
*   **Level**: `ERROR`
*   **Message**: `Transaction deadlock detected`
*   **DB Lock Time**: `1000` ms (High!)
*   **Pool Wait Time**: `400` ms
*   **Expected Root Cause**: `Database Row Contention` or `Deadlock`
*   **Mitigation**: `optimize_queries` or `kill_blocking_pid`

### 🟡 Test T-03: Redis Cache Drift
*Verify handling of auxiliary services.*

*   **Service**: `redis-cache`
*   **Latency**: `1200` ms
*   **Level**: `WARNING`
*   **Message**: `Cache miss rate > 85%`
*   **DB Lock Time**: `0` ms
*   **Pool Wait Time**: `50` ms
*   **Expected Root Cause**: `Cache Eviction Pressure` or `Cold Cache`

### 🔴 Test T-04: User Service Starvation
*Verify detection of connection pooling limits.*

*   **Service**: `user-service`
*   **Latency**: `2800` ms
*   **Level**: `ERROR`
*   **Message**: `Connection acquisition timeout`
*   **DB Lock Time**: `50` ms (Low)
*   **Pool Wait Time**: `900` ms (Critical!)
*   **Expected Root Cause**: `Connection Pool Exhaustion`
*   **Mitigation**: `scale_pool_size` or `add_read_replica`

---

## 🧠 "Bridging Logic" Stress Test (Advanced)

Use these specific "Message" inputs to test if the Groq Architect can translate physical symptoms structure.

| Symptom Message | Expected Bridge Logic |
| :--- | :--- |
| `"Water leaking from rack 4"` | **Hardware Thermal Failure** -> **Throttling** -> **Latency** |
| `"Robot arm jammed in joint 3"` | **Mechanical Interference** -> **Control Plane Timeout** |
| `"Power supply buzzing"` | **Voltage Instability** -> **Compute Errors** |

---

## ✅ Final Verification Checklist

- [ ] **Vector Count**: Does "Total Vectors" increase by 3 after each injection loop?
- [ ] **Graph Update**: Does the Causal Graph draw a line from `DB Lock` -> `Latency` in Test T-02?
- [ ] **Reasoning**: Does the "Architect Reasoning" text explain *why* it chose the diagnosis?
- [ ] **History**: Can you find these logs in the "Log History" tab using the search term "deadlock"?
