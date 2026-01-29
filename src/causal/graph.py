import networkx as nx
import pandas as pd
import asyncio
from collections import deque
from bisect import bisect_left
from typing import Dict, List, Optional
import time

class TemporalKnowledgeGraph:
    def __init__(self, max_edges: int = 5000, ttl_seconds: int = 3600):
        """
        Args:
            max_edges: Hard memory limit (8GB safety). Oldest auto-evicted.
            ttl_seconds: Edges older than this are ignored (but kept for history until max_edges hit)
        """
        # Use standard DiGraph, store temporal data as edge attributes (lists)
        # Less memory than MultiDiGraph for high-frequency edges
        self.graph = nx.DiGraph()
        self.max_edges = max_edges
        self.ttl_seconds = ttl_seconds
        
        # Thread-safe observation log for time-windowing (O(log n) query)
        self.observations: deque = deque(maxlen=max_edges)  # (timestamp, u, v, metadata)
        
        # Service state cache (node attributes)
        self.service_states: Dict[str, dict] = {}
        
        # Async lock for thread safety
        self._lock = asyncio.Lock()
        
        # Pre-allocate pandas DataFrame buffer for bulk exports (performance)
        self._export_buffer = []
    
    async def add_observation(self, 
                            from_service: str, 
                            to_service: str, 
                            latency_ms: float, 
                            timestamp: float,
                            cpu_percent: Optional[float] = None,
                            memory_percent: Optional[float] = None):
        """
        Thread-safe addition of service interaction.
        Auto-updates node states if cpu/memory provided.
        """
        async with self._lock:
            # Add/update edge with rolling window of observations
            # Note: We maintain a global observation list for time filtering, 
            # and edge-local lists for neighbor data retrieval.
            
            if not self.graph.has_edge(from_service, to_service):
                self.graph.add_edge(from_service, to_service, observations=deque(maxlen=100))
            
            # Append to edge's rolling history
            edge_data = self.graph[from_service][to_service]['observations']
            edge_data.append({
                'timestamp': timestamp,
                'latency_ms': latency_ms,
                'cpu_from': cpu_percent,
                'mem_from': memory_percent
            })
            
            # Global time index for fast windowing
            # Storing minimal info to separate index from data? 
            # User code implies keeping u, v to find edges later.
            self.observations.append((timestamp, from_service, to_service))
            
            # Update node current state if provided
            if cpu_percent is not None:
                self.service_states[from_service] = {
                    'current_cpu': cpu_percent,
                    'current_memory': memory_percent,
                    'last_updated': timestamp
                }
                # Sync to graph nodes for NetworkX algorithms
                if not self.graph.has_node(from_service):
                    self.graph.add_node(from_service)
                self.graph.nodes[from_service].update(self.service_states[from_service])
                
            if not self.graph.has_node(to_service):
                self.graph.add_node(to_service)
    
    async def get_causal_neighbors(self, 
                                 service: str, 
                                 time_window_seconds: float = 300.0,
                                 current_time: Optional[float] = None) -> Dict[str, List[dict]]:
        """
        O(log N) temporal query using binary search.
        
        Returns:
            Dict mapping upstream service -> list of observations in window
        """
        async with self._lock:
            if current_time is None:
                current_time = time.time()
            
            cutoff = current_time - time_window_seconds
            
            # Binary search for cutoff index (O(log N))
            # Convert deque to list for indexing (fast operation, C-level)
            obs_list = list(self.observations)
            if not obs_list:
                return {}
            
            # Find first index >= cutoff
            # Creating a dummy tuple for comparison since key handles the first element
            idx = bisect_left(obs_list, (cutoff,), key=lambda x: x[0]) if hasattr(bisect_left, '__code__') and 'key' in bisect_left.__code__.co_varnames else bisect_left([x[0] for x in obs_list], cutoff)
            # Actually Python 3.10+ supports key. 3.11 is installed.
            # Using direct approach as requested by user code structure
            idx = bisect_left(obs_list, cutoff, key=lambda x: x[0])
            
            recent_obs = obs_list[idx:]
            
            # Filter for edges pointing to target service
            upstream = {}
            for ts, u, v in recent_obs:
                if v == service:
                    if u not in upstream:
                        upstream[u] = []
                    # Get full metadata from graph edge
                    if self.graph.has_edge(u, v):
                        edge_obs = self.graph[u][v].get('observations', deque())
                        # Find specific observation matching timestamp
                        # Optimization: Since edge_obs is ordered by time, we could search efficiently,
                        # but linear scan of 100 items is fast enough.
                        for obs in edge_obs:
                            if abs(obs['timestamp'] - ts) < 0.001:
                                upstream[u].append(obs)
                                break
            
            return upstream
    
    def get_subgraph_for_causal_analysis(self, 
                                       target_service: str, 
                                       lookback_seconds: int = 600) -> pd.DataFrame:
        """
        Export to pandas for DoWhy integration.
        Creates time-lagged features: cpu(t-1), latency(t-1) -> error(t)
        """
        # Implementation hint for claude:
        # 1. Query all upstream of target_service
        # 2. Build panel data: rows = time windows, cols = metrics at t-1, outcome at t
        # 3. Return DataFrame ready for CausalDiscoveryEngine.discover_structure()
        pass
    
    async def prune_old_edges(self, max_age_seconds: float = 7200):
        """Memory management: Explicit cleanup of ancient history (call periodically)"""
        async with self._lock:
            cutoff = time.time() - max_age_seconds
            edges_to_remove = []
            
            for u, v, data in self.graph.edges(data=True):
                obs = data.get('observations', deque())
                # Filter old observations
                new_obs = deque((o for o in obs if o['timestamp'] > cutoff), maxlen=100)
                if len(new_obs) == 0:
                    edges_to_remove.append((u, v))
                else:
                    data['observations'] = new_obs
            
            self.graph.remove_edges_from(edges_to_remove)
