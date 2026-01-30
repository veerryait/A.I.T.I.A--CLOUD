import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import plotly.graph_objects as go
from datetime import datetime, timedelta

class LatencyForecaster:
    def __init__(self):
        # We use a Degree 2 Polynomial to capture "Acceleration" (Curves)
        # linear would miss an exponential memory leak.
        self.model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())

    def forecast(self, history_df: pd.DataFrame, future_minutes: int = 30):
        """
        Predicts future latency using Polynomial Regression (Non-Linear).
        """
        if len(history_df) < 5:
            return None, "Not enough data for prediction"
            
        # 1. Prepare Data
        # X = Seconds since start of window
        history_df = history_df.sort_values('timestamp')
        start_time = history_df['timestamp'].iloc[0]
        
        history_df['seconds'] = (history_df['timestamp'] - start_time).dt.total_seconds()
        
        X = history_df[['seconds']].values
        y = history_df['value'].values # Latency
        
        # 2. Fit Polynomial Model
        self.model.fit(X, y)
        
        # 3. Predict Future
        last_second = X[-1][0]
        future_seconds = np.array([last_second + (i * 60) for i in range(1, future_minutes + 1)]).reshape(-1, 1)
        
        future_pred = self.model.predict(future_seconds)
        
        # 4. Create Visualization
        future_timestamps = [start_time + timedelta(seconds=int(s)) for s in future_seconds.flatten()]
        
        fig = go.Figure()
        
        # Historical Line (Cyan)
        fig.add_trace(go.Scatter(
            x=history_df['timestamp'], 
            y=y,
            mode='lines+markers',
            name='Historical (Actual)',
            line=dict(color='#00e6e6', width=3) # Cyan
        ))
        
        # Forecast Line (Magenta - Dashed)
        fig.add_trace(go.Scatter(
            x=future_timestamps,
            y=future_pred,
            mode='lines',
            name='AI Forecast (Polynomial)',
            line=dict(color='#ff00ff', width=3, dash='dot') # Magenta
        ))
        
        # SLO Threshold (Red)
        fig.add_axhline(y=1000, line_dash="dash", line_color="red", annotation_text="SLO Breach Risk (1000ms)")
        
        fig.update_layout(
             title="🔮 Non-Linear Latency Forecasting (Polynomial Degree 2)",
             xaxis_title="Time",
             yaxis_title="Latency (ms)",
             template="plotly_dark",
             height=400,
             margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # 5. Analysis
        max_pred = max(future_pred)
        breach = max_pred > 1000
        
        return fig, {
            "max_predicted_latency": round(max_pred, 2),
            "will_breach_slo": bool(breach),
            "trend": "Accelerating 🚀" if future_pred[-1] > future_pred[0] * 1.1 else "Stable"
        }
