import asyncio
import pytest
import time
from src.causal.graph import TemporalKnowledgeGraph

@pytest.mark.asyncio
async def test_temporal_graph_basics():
    print("\n🚀 Starting Temporal Graph Basics Test")
    graph = TemporalKnowledgeGraph(max_edges=100, ttl_seconds=30)
    
    # 1. Add observations (Chronological order required for bisect optimization)
    now = time.time()
    # Oldest first
    await graph.add_observation("ServiceA", "ServiceB", latency_ms=10.0, timestamp=now - 20)
    await graph.add_observation("ServiceA", "ServiceB", latency_ms=10.5, timestamp=now - 5)
    await graph.add_observation("ServiceC", "ServiceB", latency_ms=20.0, timestamp=now - 2)
    await graph.add_observation("ServiceA", "ServiceB", latency_ms=12.0, timestamp=now - 1, cpu_percent=55.0)
    
    # 2. Verify graph structure
    assert graph.graph.number_of_nodes() == 3
    assert graph.graph.number_of_edges() == 2 # A->B, C->B
    
    # Verify node attributes
    assert graph.graph.nodes["ServiceA"]["current_cpu"] == 55.0 # Latest update
    
    # 3. Query Neighbors (Window = 3 seconds)
    neighbors = await graph.get_causal_neighbors("ServiceB", time_window_seconds=3.0, current_time=now)
    
    print(f"Neighbors for ServiceB (last 3s): {neighbors.keys()}")
    
    # Expect ServiceC (t-2) and ServiceA (t-1). 
    # ServiceA (t-5) and (t-20) should be excluded.
    assert "ServiceC" in neighbors
    assert "ServiceA" in neighbors
    
    # Search specific observations
    obs_A = neighbors["ServiceA"]
    # We expect only the one at t-1 (t-5 is > 3s ago)
    print(f"Observations from ServiceA: {[o['timestamp'] for o in obs_A]}")
    assert len(obs_A) == 1
    assert abs(obs_A[0]['timestamp'] - (now - 1)) < 0.001
    
    print("✅ Basics Test Passed")

@pytest.mark.asyncio
async def test_concurrency():
    print("\n🚀 Starting Concurrency Test")
    graph = TemporalKnowledgeGraph()
    
    async def worker(id):
        for i in range(100):
            await graph.add_observation(f"S{id}", "Target", 10, time.time())
            
    # Run 5 workers concurrently
    await asyncio.gather(*(worker(i) for i in range(5)))
    
    # Check edges
    assert graph.graph.number_of_nodes() == 6 # S0..S4 + Target
    neighbors = await graph.get_causal_neighbors("Target", time_window_seconds=10)
    total_obs = sum(len(obs) for obs in neighbors.values())
    print(f"Total observations recorded: {total_obs}")
    assert total_obs == 500
    print("✅ Concurrency Test Passed")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_temporal_graph_basics())
    loop.run_until_complete(test_concurrency())
    loop.close()
