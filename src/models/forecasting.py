import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from datetime import datetime, timedelta

class LatencyForecaster:
    def __init__(self):
        self.model = LinearRegression()

    def forecast_next_hour(self, history_df):
        """
        Takes a DataFrame with 'timestamp' and 'latency_ms'.
        Returns a DataFrame with original data + 30 mins of future predictions.
        """
        if history_df.empty or len(history_df) < 5:
            return None, None

        # Prepare Data
        df = history_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create numerical time feature (seconds since start)
        start_time = df['timestamp'].min()
        df['seconds'] = (df['timestamp'] - start_time).dt.total_seconds()
        
        # Fit Model
        X = df[['seconds']].values
        y = df['latency_ms'].values
        self.model.fit(X, y)
        
        # Predict Future (next 30 mins = 1800 seconds)
        last_second = df['seconds'].max()
        future_seconds = np.array([last_second + i*60 for i in range(1, 31)]).reshape(-1, 1)
        future_latency = self.model.predict(future_seconds)
        
        # Construct Future DataFrame
        future_dates = [df['timestamp'].max() + timedelta(minutes=i) for i in range(1, 31)]
        
        future_df = pd.DataFrame({
            'timestamp': future_dates,
            'latency_ms': future_latency,
            'type': 'forecast'
        })
        
        # Plotting
        fig = go.Figure()
        
        # Historical Data
        fig.add_trace(go.Scatter(
            x=df['timestamp'], 
            y=df['latency_ms'],
            mode='lines+markers',
            name='Historical (Actual)',
            line=dict(color='#00ffff', width=2)
        ))
        
        # Forecast Data
        fig.add_trace(go.Scatter(
            x=future_df['timestamp'], 
            y=future_df['latency_ms'],
            mode='lines',
            name='AI Forecast (Projected)',
            line=dict(color='#ff00ff', width=2, dash='dot')
        ))
        
        # Threshold Line (e.g., 500ms SLO)
        fig.add_hline(y=1000, line_dash="dash", line_color="red", annotation_text="SLO Breach Risk (1000ms)")
        
        fig.update_layout(
            title="🔮 Latency Trend Forecasting (Linear Projection)",
            template="plotly_dark",
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return future_df, fig
