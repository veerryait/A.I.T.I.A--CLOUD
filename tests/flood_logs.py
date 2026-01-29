import requests
import random
from datetime import datetime
import time

for i in range(100):
    payload = {
        "timestamp": datetime.now().isoformat(),
        "service": random.choice(['payment-db', 'api-gateway']),
        "latency": random.randint(20, 3000),
        "message": random.choice(["OK", "Timeout", "Slow query"]),
        "level": "INFO"
    }
    try:
        requests.post("http://localhost:8000/ingest/log", json=payload)
        print(f"Sent {i}")
    except Exception as e:
        print(f"Failed to send {i}: {e}")
    time.sleep(0.1)
