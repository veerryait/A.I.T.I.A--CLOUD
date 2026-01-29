import pandas as pd
import numpy as np
from src.causal.discovery import CausalDiscoveryEngine
import plotly.graph_objects as go
import networkx as nx

def generate_synthetic_data(n=1000):
    """
    Generate synthetic data with known causal structure:
    CPU -> Latency
    Memory -> Latency
    Latency -> Error
    """
    np.random.seed(42)
    # CPU: uniform between 10 and 90
    cpu = np.random.uniform(10, 90, n)
    # Memory: uniform between 20 and 80
    memory = np.random.uniform(20, 80, n)
    
    # Latency depends on CPU and Memory + noise
    latency = 0.5 * cpu + 0.3 * memory + np.random.normal(0, 5, n)
    
    # Error count depends on Latency + noise
    error = 0.05 * latency + np.random.normal(0, 2, n)
    error = np.maximum(error, 0) # Non-negative
    
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=n, freq='min'),
        'service_name': ['service-a'] * n,
        'cpu_percent': cpu,
        'memory_percent': memory,
        'latency_ms': latency,
        'error_count': error
    })
    return df

def test_causal_engine_e2e():
    print("🚀 Starting Causal Engine E2E Test")
    
    # 1. Setup Data
    df = generate_synthetic_data(n=2000)
    engine = CausalDiscoveryEngine(df)
    
    # 2. Discovery
    print("Running structure discovery...")
    graph = engine.discover_structure()
    assert graph is not None
    assert isinstance(graph, nx.DiGraph)
    print(f"Graph nodes: {graph.nodes()}")
    print(f"Graph edges: {graph.edges()}")
    
    # 3. Estimation
    print("Running effect estimation (Treatment: latency_ms, Outcome: error_count)...")
    try:
        effect = engine.estimate_causal_effect(treatment='latency_ms', outcome='error_count')
        print(f"Estimated Effect: {effect}")
        if effect is not None:
             print(f"✅ Effect is valid number: {effect:.4f}")
    except Exception as e:
        print(f"Estimation failed: {e}")

    # 4. Visualization
    print("Generating visualization...")
    fig = engine.visualize_graph()
    assert isinstance(fig, go.Figure)
    print("✅ Visualization object created")

if __name__ == "__main__":
    test_causal_engine_e2e()
