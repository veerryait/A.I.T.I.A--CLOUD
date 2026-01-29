import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class MicroserviceDataGenerator:
    """
    Generates logs with TRUE causal structure:
    DB_Throttle -> Connection_Pool_Wait -> API_Latency -> Error_Rate
    """
    def __init__(self, n_services=5, n_logs=5000):
        self.services = ['api-gateway', 'user-service', 'payment-db', 
                        'redis-cache', 'notification-svc']
        self.n_logs = n_logs
        self.start_time = datetime.now() - timedelta(hours=24)
        
    def generate(self):
        logs = []
        
        # Generate base traffic pattern
        base_time = self.start_time
        incident_start = base_time + timedelta(hours=18)  # Cascade starts at hour 18
        
        for i in range(self.n_logs):
            timestamp = base_time + timedelta(seconds=i*30)  # ~30s interval to cover >24h with 3000 logs
            
            # CAUSAL INJECTION: At hour 18, DB gets slow
            is_incident = timestamp > incident_start
            
            # Root Cause: DB Lock Contention (exogenous shock)
            if is_incident:
                db_lock = np.random.exponential(2.0)  # High lock time
            else:
                db_lock = np.random.exponential(0.1)  # Normal
                
            # Causal Chain 1: Lock -> Connection Pool Exhaustion
            pool_wait = 50 * db_lock + np.random.normal(0, 10)
            pool_wait = max(0, pool_wait)
            
            # Causal Chain 2: Pool Wait -> API Latency
            latency = 20 + (2 * pool_wait) + np.random.exponential(10)
            
            # Causal Chain 3: Latency -> Errors (threshold effect)
            error_prob = 1 / (1 + np.exp(-(latency - 200)/50))  # Sigmoid
            is_error = np.random.random() < error_prob
            
            # Select service (weighted toward affected ones during incident)
            if is_incident and np.random.random() > 0.3:
                service = np.random.choice(['payment-db', 'api-gateway', 'user-service'])
            else:
                service = np.random.choice(self.services)
                
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'service': service,
                'db_lock_time': float(db_lock),
                'pool_wait_ms': float(pool_wait),
                'latency_ms': float(latency),
                'error_count': 1 if is_error else 0,
                'level': 'ERROR' if is_error else ('WARN' if latency > 100 else 'INFO'),
                'message': f"Request completed in {int(latency)}ms" if not is_error else "Request timeout"
            }
            logs.append(log_entry)
            
        df = pd.DataFrame(logs)
        
        # Ensure data/raw directory exists
        os.makedirs('data/raw', exist_ok=True)
        
        # Save ground truth for verification
        df.to_csv('data/raw/synthetic_logs.csv', index=False)
        return df

if __name__ == "__main__":
    gen = MicroserviceDataGenerator(n_logs=3000)  # 3000 = safe for 8GB
    df = gen.generate()
    print(f"Generated {len(df)} logs with causal ground truth")
    print(f"Error rate: {df['error_count'].mean():.2%}")
    print(f"DB Lock correlation with Errors: {df[['db_lock_time', 'error_count']].corr().iloc[0,1]:.2f}")
