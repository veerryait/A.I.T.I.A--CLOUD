import requests
import time
from datetime import datetime

# Configuration matching user request
payload = {
    "timestamp": "", # Will set dynamically
    "service": "payment-db",
    "latency": 4000,
    "message": "Connection timeout waiting for pool",
    "level": "ERROR"
}

print("Injecting 5 high-latency error logs to trigger anomaly detection...")

for i in range(5):
    payload["timestamp"] = datetime.now().isoformat()
    try:
        resp = requests.post("http://localhost:8000/ingest/log", json=payload)
        print(f"Injection {i+1}: Status {resp.status_code}")
    except Exception as e:
        print(f"Injection {i+1} Failed: {e}")
    time.sleep(0.5) # Rapid injections

print("Done. Check API Server logs for 'Anomaly detected' and 'EXECUTING'.")
