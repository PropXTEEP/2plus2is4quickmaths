import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import time
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="LBRT Stock Watcher",
    page_icon="📈",
    layout="wide"
)

# 2. Sidebar Controls
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 30)
stop_button = st.sidebar.button("Stop Watching")

# 3. Functions
def get_lbrt_data():
    """Fetches the latest minute-level data for LBRT"""
    ticker = "LBRT"
    # Get 1 day of data with 1-minute intervals to see intraday movement
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    
    # yfinance sometimes returns a multi-level index, we flatten it if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

def plot_chart(df):
    """Creates a simple interactive candle/line chart"""
    fig = go.Figure()
    
    # Add the close price line
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'], 
        mode='lines', 
        name='Price',
        line=dict(color='#00CC96', width=2)
    ))

    fig.update_layout(
        title="LBRT Intraday Price (1-Minute Intervals)",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig

# 4. Main App Layout
st.title("🦅 LBRT Real-Time Watcher")

# We use a placeholder container so we can update just this area
placeholder = st.empty()

# 5. The "Watch" Loop
# This loop will run indefinitely until "Stop Watching" is clicked
if not stop_button:
    while True:
        with placeholder.container():
            # A. Fetch Data
            df = get_lbrt_data()
            
            if not df.empty:
                latest_price = df['Close'].iloc[-1]
                start_price = df['Open'].iloc[0]
                price_change = latest_price - start_price
                pct_change = (price_change / start_price) * 100
                current_time = datetime.now().strftime("%H:%M:%S")

                # B. Metrics Row
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", f"${latest_price:.2f}")
                col2
