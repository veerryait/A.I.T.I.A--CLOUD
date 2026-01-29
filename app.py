import streamlit as st
import os
import json
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import A.I.T.I.A components
from src.models.memory import HybridLogStore
import src.models.groq_client as groq_mod
import importlib
from src.causal.discovery import CausalDiscoveryEngine

# Force reload the AI brain on every run
importlib.reload(groq_mod)
GroqDiagnostician = groq_mod.GroqDiagnostician

# 1. Explicit HF Detection + /data Path
if os.path.exists("/data"):
    os.environ["HF_SPACE"] = "1"
    CHROMA_PATH = "/data/chroma"
else:
    CHROMA_PATH = "./data/chroma"

# Page Config
st.set_page_config(layout="wide", page_title=f"A.I.T.I.A | v2.4 ({time.strftime('%H:%M:%S')})")

# 2. Caching Decorators (Prevents Memory Explosion)
@st.cache_resource
def get_vector_store():
    return HybridLogStore(persist_dir=CHROMA_PATH)

@st.cache_resource
def get_causal_engine():
    return CausalDiscoveryEngine()

# 3. Versioning & Freshness Check (Moved to Footer to prevent Sidebar auto-open)
# st.sidebar.success("✅ ACTIVE: SRE ARCHITECT v3.0")
# st.sidebar.caption(f"Last Boot: {datetime.now().strftime('%H:%M:%S')}")

def get_fresh_diagnostician():
    api_key = os.getenv("GROQ_API_KEY")
    return GroqDiagnostician(api_key=api_key) if api_key else None

# Check key immediately
if not os.getenv("GROQ_API_KEY"):
    st.error("🔴 Missing GROQ_API_KEY")
    st.stop()

# 4. Custom Styling (Premium Aesthetics)
st.markdown("""
<style>
    .glow-card {
        background: rgba(25, 25, 25, 0.7);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .glow-title {
        color: #00ffff;
        font-family: 'Inter', sans-serif;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .action-box {
        background: rgba(0, 255, 255, 0.05);
        border-left: 4px solid #00ffff;
        padding: 10px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
memory = get_vector_store()
causal_engine = get_causal_engine()

# UI Header
st.title("🧠 A.I.T.I.A")
st.markdown("<h3 style='text-align: left; color: #aaaaaa;'>Autonomous Investigation & Treatment of Infrastructure Anomalies</h3>", unsafe_allow_html=True)

# Top-Level Navigation
main_tab, guide_tab = st.tabs(["🚀 Control Plane", "📖 User Guide"])

with guide_tab:
    st.markdown("""
    ### 📖 How to Use A.I.T.I.A
    Welcome to the Autonomous SRE Agent. Here is a guide to the controls and metrics.

    #### 1. Ingest Log (Simulation)
    Use this form to inject synthetic logs into the system to test the AI's reasoning.
    - **Service**: The microservice reporting the log (e.g., `payment-db`, `api-gateway`).
    - **Latency (ms)**: The response time of the request. High latency (>500ms) often triggers alerts.
    - **Level**: The severity (`INFO`, `WARNING`, `ERROR`). The AI prioritizes `ERROR` logs.
    - **Message**: The text content. Try specific technical errors or physical symptoms like *"Water leaking from rack"*.
    - **DB Lock Time (ms)**: Amount of time a database transaction was blocked. High lock time implies contention.
    - **Pool Wait Time (ms)**: Amount of time waiting for a free database connection. High wait time implies resource exhaustion.

    #### 2. Analysis & Diagnosis
    - **Inject Signal**: Commits your log to the semantic memory (Vector Store).
    - **🚀 Analyze Now**: Triggers the Causal Engine and the Groq AI "Architect".
        - It builds a Causal Graph from recent data.
        - It calculates the **True Causal Effect** of resource waits on errors.
        - It asks the LLM to diagnose the root cause and suggest a CLI fix.

    #### 3. Metrics Explained
    - **Total Vectors**: The total number of logs currently stored in the system memory.
    - **Errors Detected**: The count of logs marked as `ERROR` in the visible history.
    - **Causal Graph**: A visual map showing the statistical relationships between your metrics (e.g., Does *Lock Time* cause *Latency*?).

    ---
    *Tip: To test the "Bridging Logic", try injecting a non-technical message like "Robot arm stuck" and see if the AI can translate it to a software issue.*
    """)

with main_tab:
    col1, col2 = st.columns([1, 2])
    
    # SECTION 1: Ingest Log
    with col1:
        st.subheader("📥 Ingest Log")
        with st.form("log_form", clear_on_submit=False):
            svc = st.selectbox("Service", ['api-gateway', 'user-service', 'payment-db', 'redis-cache'])
            lat = st.slider("Latency (ms)", 0, 5000, 100)
            lvl = st.selectbox("Level", ["INFO", "ERROR", "WARNING", "DEBUG"], index=0)
            msg = st.text_input("Message", "Request processed")
            
            # Additional fields for causal engine
            db_lock = st.slider("DB Lock Time (ms)", 0, 1000, 0)
            pool_wait = st.slider("Pool Wait Time (ms)", 0, 500, 0)
            
            submitted = st.form_submit_button("Inject Signal")
            
            if submitted:
                # Sync ingestion into ChromaDB
                memory.collection.add(
                    ids=[f"{datetime.now().isoformat()}_{svc}"],
                    embeddings=[memory.encoder.encode([msg])[0].tolist()],
                    metadatas=[{
                        'service': svc,
                        'timestamp': datetime.now().isoformat(),
                        'level': lvl,
                        'latency_ms': float(lat),
                        'db_lock_time': float(db_lock),
                        'pool_wait_ms': float(pool_wait),
                        'error_count': 1 if lvl == "ERROR" else 0 
                    }],
                    documents=[msg]
                )
                st.success(f"Signal ingested for {svc}")
                time.sleep(0.5)
                st.rerun()

        # SECTION 2: System Status
        st.divider()
        st.subheader("📊 System Status")
        try:
            count = memory.collection.count()
            st.metric("Total Vectors (Logs)", count)
            
            # Simple error count logic
            recent_logs = memory.collection.get(include=['metadatas'])
            errors = sum(1 for m in recent_logs['metadatas'] if m.get('error_count', 0) > 0)
            st.metric("Total Errors Detected", errors)
        except Exception as e:
            st.error(f"Status failed: {e}")

        # SECTION 2.1: Danger Zone (Privacy)
        st.divider()
        with st.expander("⚠️ Danger Zone"):
            st.warning("Erase All Historical Data. This cannot be undone.")
            confirm = st.checkbox("I confirm I want to wipe all logs")
            if st.button("🗑️ Clear All Memory", type="primary", disabled=not confirm):
                if memory.flush_all_history():
                    st.success("Memory wiped clean!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to clear memory.")

    # SECTION 3: AI Investigation & History
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔍 Investigation", "📜 Log History", "📈 Forecast"])
        
        with tab1:
            # Analyze Now Button with Rate Limit Protection
            if st.button("🚀 Analyze Now", use_container_width=True):
                with st.spinner("Analyzing causal patterns and querying Groq..."):
                    # 5. Rate Limit Protection / Delay
                    time.sleep(0.5)
                    
                    # Fetch recent errors
                    recent_errors = memory.get_recent_errors(30) # last 30 mins
                    
                    if recent_errors.empty:
                        st.warning("No recent errors found to analyze. Try injecting some ERROR logs first.")
                    else:
                        # 1. Build Causal Model
                        all_raw = memory.collection.get()['metadatas']
                        if not all_raw:
                            st.error("No data available in vector store to build causal model.")
                            st.stop()
                            
                        all_data = pd.DataFrame(all_raw)
                        
                        # Robust Data Cleaning for Causal Engine
                        causal_cols = ['db_lock_time', 'pool_wait_ms', 'latency_ms', 'error_count']
                        for col in causal_cols:
                            if col in all_data.columns:
                                all_data[col] = pd.to_numeric(all_data[col], errors='coerce')
                        
                        # Drop rows with NaNs in critical columns and reset index
                        all_data = all_data.dropna(subset=causal_cols).reset_index(drop=True)
                        
                        if len(all_data) < 5:
                            st.warning("Insufficient cleaned data (need at least 5 records) to build causal model. Try injecting more logs.")
                            st.stop()

                        causal_engine.build_model(all_data)
                        ate = causal_engine.estimate_effect()
                        
                        # 2. Build Context for LLM
                        # Focus on the ABSOLUTE LATEST service that produced an error
                        recent_errors = recent_errors.sort_values('timestamp', ascending=False)
                        latest_event = recent_errors.iloc[0]
                        target_svc = latest_event['service']
                        
                        similar = memory.query_similar_incidents(latest_event['message'], target_svc, 3)
                        
                        context = {
                            "incident_telemetry": {
                                "service": target_svc,
                                "non_technical_symptom_text": latest_event['message'],
                                "telemetry_sensors": {
                                    "latency_ms": latest_event['latency_ms'],
                                    "db_lock_time": latest_event.get('db_lock_time', 0),
                                    "pool_wait_ms": latest_event.get('pool_wait_ms', 0)
                                }
                            },
                            "causal_statistical_model": {
                                "avg_latency_last_30m": recent_errors['latency_ms'].mean(),
                                "total_errors_last_30m": len(recent_errors),
                                "causal_effect_ate": f"{ate:.4f} errors per ms pool wait"
                            },
                            "historical_context_raw": {
                                "recent_logs": recent_errors['message'].unique()[:5].tolist(),
                                "semantically_similar_past_incidents": [s['message'] for s in similar]
                            }
                        }
                        
                        # 3. Request Diagnosis from Groq
                        diagnoser = get_fresh_diagnostician()
                        diagnosis = diagnoser.diagnose(context)
                        
                        # Store in session state for persistence
                        st.session_state['last_analysis'] = {
                            'diagnosis': diagnosis,
                            'context': context,
                            'timestamp': datetime.now().isoformat()
                        }
                        
            # 4. Render Result (Persistent) & Feedback Loop
            if 'last_analysis' in st.session_state:
                analysis = st.session_state['last_analysis']['diagnosis']
                
                root_cause = analysis.get('SRE_DIAGNOSIS', 'Unknown')
                confidence = analysis.get('CONFIDENCE', 0)
                action = analysis.get('CLI_MITIGATION', 'N/A')
                reasoning = analysis.get('CAUSAL_BRIDGE', 'No reasoning provided.')
                if isinstance(reasoning, list):
                    reasoning = "\n- ".join(reasoning)
                affected = analysis.get('SERVICE', 'N/A')

                st.markdown(f"""
                <div class="glow-card">
                    <div class="glow-title">🦉 SRE ARCHITECT ANALYSIS</div>
                    <div style="margin-bottom: 20px;">
                        <strong style="color: #00ffff;">SRE Root Cause</strong>: {root_cause}<br>
                        <span style="font-size: 28px; font-weight: 800; color: #ffffff;">{confidence*100:.0f}% <span style="font-size: 14px; opacity: 0.6;">Confidence</span></span>
                    </div>
                    <div class="action-box">
                        <strong>Targeted CLI Mitigation</strong>: <code>{action}</code>
                    </div>
                    <p style="opacity: 0.9; margin-top: 15px;"><strong>Architect Reasoning (The Bridge)</strong>:<br>{reasoning}</p>
                    <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 12px; opacity: 0.7;">
                        AFFECTED SERVICE: {affected.upper()}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Feedback Loop (Active Learning)
                fc1, fc2 = st.columns([1, 6])
                with fc1:
                    if st.button("👍 Correct", key="btn_correct"):
                        with open("data/feedback_dataset.jsonl", "a") as f:
                            entry = {"timestamp": datetime.now().isoformat(), "rating": "positive", "analysis": analysis}
                            f.write(json.dumps(entry) + "\n")
                        st.toast("Feedback saved! Model reinforced.")
                with fc2:
                    if st.button("👎 Incorrect", key="btn_incorrect"):
                        with open("data/feedback_dataset.jsonl", "a") as f:
                            entry = {"timestamp": datetime.now().isoformat(), "rating": "negative", "analysis": analysis}
                            f.write(json.dumps(entry) + "\n")
                        st.toast("Flagged for review.")

        with tab2:
            st.markdown("### 🔎 Search Past Incidents")
            c1, c2, c3 = st.columns([2, 1, 1])
            q_text = c1.text_input("Search message (Semantic)", placeholder="e.g. timeout or database lock")
            q_svc = c2.selectbox("Filter Service", ['All', 'api-gateway', 'user-service', 'payment-db', 'redis-cache'], index=0)
            q_n = c3.number_input("Limit", 5, 50, 10, step=5)
            
            search_svc = None if q_svc == 'All' else q_svc
            
            if q_text:
                results = memory.query_similar_incidents(q_text, service=search_svc, n=q_n)
                if results:
                    for r in results:
                        with st.expander(f"📌 {r['metadata']['service']} | {r['metadata']['timestamp'][:16]} (Score: {r['similarity_score']:.2f})"):
                            st.write(f"**Message**: `{r['message']}`")
                            st.json(r['metadata'])
                else:
                    st.info("No matching incidents found.")
            else:
                # Show absolute recent logs if no query
                st.info("Enter a search term above to find semantically similar past incidents.")
                recent = memory.collection.get(limit=q_n, include=['metadatas', 'documents'])
                if recent['ids']:
                    for i in range(len(recent['ids'])):
                        with st.expander(f"📜 {recent['metadatas'][i]['service']} | {recent['metadatas'][i]['timestamp'][:16]}"):
                            st.write(f"**Message**: `{recent['documents'][i]}`")
                            st.json(recent['metadatas'][i])

        with tab3:
            st.subheader("🔮 Latency Forecasting")
            st.caption("Linear regression projection of service latency (Next 30 mins).")
            
            from src.models.forecasting import LatencyForecaster
            forecaster = LatencyForecaster()
            
            # Get raw data
            all_logs = memory.collection.get(include=['metadatas'])
            if all_logs['metadatas']:
                df = pd.DataFrame(all_logs['metadatas'])
                # Safe casting
                if 'latency_ms' in df.columns:
                    df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
                
                if 'latency_ms' in df.columns and 'timestamp' in df.columns:
                     try:
                        future, fig_forecast = forecaster.forecast_next_hour(df)
                        if fig_forecast:
                            st.plotly_chart(fig_forecast, use_container_width=True)
                            
                            # AI Risk Assessment
                            if future is not None:
                                max_pred = future['latency_ms'].max()
                                if max_pred > 1000:
                                    st.error(f"⚠️ PREDICTION: Latency expected to breach 1000ms SLO in next 30 mins (Max: {max_pred:.0f}ms)")
                                else:
                                    st.success("✅ PREDICTION: System stable. No SLO breach expected.")
                        else:
                            st.info("Not enough data to forecast (Need > 5 records).")
                     except Exception as e:
                         st.warning(f"Forecasting error: {e}")
                else:
                    st.info("No valid latency data available.")
            else:
                 st.info("Ingest data to see forecasts.")

        # Causal Graph Visualization
        st.divider()
        st.subheader("🕸️ Infrastructure Causal Graph")
        fig = causal_engine.get_causal_graph_viz()
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center'>
    <small>A.I.T.I.A Control Plane | Built with DoWhy & Groq | Persistence: ON</small>
</div>
""", unsafe_allow_html=True)
