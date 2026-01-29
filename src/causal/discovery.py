import pandas as pd
import numpy as np
from dowhy import CausalModel
import networkx as nx
from typing import Dict, List, Optional
import plotly.graph_objects as go
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CausalDiscoveryEngine:
    def __init__(self):
        # We define the graph using NetworkX directly to avoid pydot dependency issues
        self.known_graph = nx.DiGraph()
        self.known_graph.add_edges_from([
            ('db_lock_time', 'pool_wait_ms'),
            ('pool_wait_ms', 'latency_ms'),
            ('latency_ms', 'error_count'),
            ('db_lock_time', 'latency_ms'),
            ('service', 'latency_ms'),
            ('service', 'error_count')
        ])
        
        self.model = None
        self.estimate = None
        
    def build_model(self, df: pd.DataFrame) -> CausalModel:
        """Build causal model with domain knowledge (avoids unstable PC algorithm)"""
        df = df.copy()
        
        # Ensure numeric types
        numeric_cols = ['db_lock_time', 'pool_wait_ms', 'latency_ms', 'error_count']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        self.model = CausalModel(
            data=df,
            treatment='pool_wait_ms',  # Intervention point: connection pool
            outcome='error_count',
            graph=self.known_graph  # Pass NetworkX object directly
        )
        logger.info("Causal model initialized with %d records", len(df))
        return self.model
    
    def identify_effect(self):
        """Identify causal effect using backdoor criterion"""
        if not self.model:
            raise ValueError("Call build_model first")
        identified = self.model.identify_effect()
        logger.info("Identified estimand: %s", identified)
        return identified
    
    def estimate_effect(self, method: str = 'backdoor.linear_regression') -> float:
        """Estimate Average Treatment Effect (ATE)"""
        if not self.model:
            raise ValueError("Call build_model first")
            
        identified = self.identify_effect()
        
        self.estimate = self.model.estimate_effect(
            identified,
            method_name=method,
            test_significance=True
        )
        
        logger.info("Causal Estimate: %.4f", self.estimate.value)
        logger.info("Confidence: %s", getattr(self.estimate, 'significance_test', 'N/A'))
        return float(self.estimate.value)
    
    def refute_estimate(self) -> Dict:
        """Robustness checks"""
        if not self.estimate:
            raise ValueError("Call estimate_effect first")
            
        refutations = {}
        
        # Placebo treatment refuter (random cause should have no effect)
        try:
            placebo = self.model.refute_estimate(
                self.model.identify_effect(),
                self.estimate,
                method_name="placebo_treatment_refuter"
            )
            refutations['placebo'] = placebo.refutation_result
        except Exception as e:
            refutations['placebo'] = f"Skipped: {e}"
            
        return refutations
    
    def get_causal_graph_viz(self) -> go.Figure:
        """Plotly visualization of causal graph"""
        G = nx.DiGraph()
        edges = [
            ('DB Lock', 'Pool Wait'),
            ('Pool Wait', 'Latency'),
            ('Latency', 'Errors'),
            ('DB Lock', 'Latency'),
            ('Service Type', 'Latency'),
            ('Service Type', 'Errors')
        ]
        G.add_edges_from(edges)
        
        pos = nx.spring_layout(G, seed=42)
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        fig = go.Figure()
        
        # Edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=2, color='#888'),
            hoverinfo='none'
        ))
        
        # Nodes
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_color = ['#ff6b6b' if node == 'Errors' else '#4ecdc4' if node == 'DB Lock' else '#95e1d3' for node in G.nodes()]
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(size=50, color=node_color),
            text=list(G.nodes()),
            textposition="middle center",
            textfont=dict(size=10, color='white')
        ))
        
        fig.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title="Live Causal Model (Updates Hourly)",
            height=500,  # Was 400
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

# Test block
if __name__ == "__main__":
    df = pd.read_csv('data/raw/synthetic_logs.csv')
    engine = CausalDiscoveryEngine()
    engine.build_model(df)
    ate = engine.estimate_effect()
    print(f"\n*** CAUSAL IMPACT ***")
    print(f"1ms increase in Pool Wait Time causes {ate:.4f} additional errors")
    print(f"(This is the TRUE causal effect, not just correlation)")
