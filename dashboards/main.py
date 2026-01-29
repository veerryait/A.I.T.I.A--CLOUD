import streamlit as st
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

import os

st.set_page_config(layout="wide", page_title="A.I.T.I.A")

API_BASE = os.getenv("API_URL", "http://localhost:8000")

st.title("🧠 A.I.T.I.A")
st.caption("Autonomous Investigation & Treatment of Infrastructure Anomalies")

# Auto-refresh every 5 seconds to catch background updates
st_autorefresh(interval=5000, key="fizzbuzzcounter")

col1, col2, col3 = st.columns([1,1,1])

with col1:
    st.subheader("Ingest Log")
    with st.form("log_form"):
        svc = st.selectbox("Service", ['api-gateway', 'user-service', 'payment-db', 'redis-cache'])
        lat = st.slider("Latency (ms)", 0, 5000, 100)
        lvl = st.selectbox("Level", ["INFO", "ERROR", "WARNING", "DEBUG"], index=0)
        msg = st.text_input("Message", "Request processed")
        submitted = st.form_submit_button("Inject")
        
        if submitted:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "service": svc,
                "latency": lat,
                "message": msg,
                "level": lvl
            }
            try:
                resp = requests.post(f"{API_BASE}/ingest/log", json=payload)
                if resp.status_code == 200:
                    st.success(f"Queued. Depth: {resp.json()['queue_size']}")
                    st.rerun()
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")

with col2:
    st.subheader("System Status")
    try:
        status = requests.get(f"{API_BASE}/status").json()
        st.metric("Vectors Stored", status['vector_count'])
        st.metric("Processed", status['processed_logs'])
        st.metric("Queue Depth", status['queue_depth'])
    except:
        st.error("API Offline")

with col3:
    st.subheader("Investigate")
    query = st.text_input("Search logs", "timeout error")
    if query:
        try:
            results = requests.get(f"{API_BASE}/query/similar", params={"q": query}).json()
            if 'results' in results and results['results']:
                for r in results['results'][:3]:
                    st.write(f"**{r['metadata']['service']}**: {r['message'][:50]}... (Score: {r['similarity_score']:.2f})")
            else:
                st.info("No matching logs found in memory.")
        except Exception as e:
             st.error(f"Search failed: {e}")

    st.divider()
    st.subheader("Recent AI Actions")
    try:
        actions = requests.get(f"{API_BASE}/remediations").json().get('history', [])
        if not actions:
            st.info("Waiting for anomaly detection...")
        for a in reversed(actions):
            with st.expander(f"🚀 {a['action']} on {a['target']}", expanded=True):
                st.write(f"**Reason**: {a['reason']}")
                st.caption(f"Time: {a['timestamp']}")
    except:
        st.write("History unavailable")

    if st.button("Clear AI Cards", help="Remove only the diagnosis cards"):
        try:
            requests.delete(f"{API_BASE}/remediations")
            st.success("Cards cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to clear: {e}")

    if st.button("🚨 Wipe All Memory", help="Delete all logs and reset everything"):
        try:
            requests.delete(f"{API_BASE}/memory")
            st.warning("System Reset!")
            st.rerun()
        except Exception as e:
            st.error(f"Reset failed: {e}")

# Causal Graph Visualization
st.subheader("Current Causal Model")
try:
    graph_data = requests.get(f"{API_BASE}/graph/causal").json()
    if 'data' in graph_data:
        fig = go.Figure(graph_data['data'])
        st.plotly_chart(fig, use_container_width=True)
    else:
         st.write("No graph data available")
except Exception as e:
    st.info("Building causal model... ingest more data first.")
