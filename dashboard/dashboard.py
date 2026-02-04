#!/usr/bin/env python3
"""
NPK Sensor Dashboard - Streamlit
Local monitoring dashboard for NPK sensor data
"""

import streamlit as st
import yaml
import time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from npk_reader import NPKSensorReader
from mqtt_publisher import ThingsBoardMQTTPublisher

# Page configuration
st.set_page_config(
    page_title="NPK Sensor Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .status-connected {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-disconnected {
        color: #F44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration
@st.cache_resource
def load_config():
    """Load configuration file"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    if not config_path.exists():
        config_path = Path('/etc/npk-monitor/config.yaml')
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Initialize sensor
@st.cache_resource
def init_sensor(config):
    """Initialize NPK sensor"""
    try:
        sensor_config = config['sensor']
        sensor = NPKSensorReader(
            port=sensor_config.get('port', '/dev/ttyS0'),
            slave_id=sensor_config.get('slave_id', 1),
            baudrate=sensor_config.get('baudrate', 4800),
            timeout=sensor_config.get('timeout', 1.0),
            registers=sensor_config.get('registers')
        )
        return sensor
    except Exception as e:
        st.error(f"Failed to initialize sensor: {e}")
        return None

# Initialize MQTT publisher
@st.cache_resource
def init_publisher(config):
    """Initialize MQTT publisher"""
    try:
        mqtt_config = config['mqtt']
        tb_config = config['thingsboard']
        
        publisher = ThingsBoardMQTTPublisher(
            host=tb_config['host'],
            port=mqtt_config.get('port', 1883),
            access_token=tb_config['access_token'],
            keepalive=mqtt_config.get('keepalive', 60),
            qos=mqtt_config.get('qos', 1)
        )
        return publisher
    except Exception as e:
        st.error(f"Failed to initialize publisher: {e}")
        return None

def create_gauge_chart(value, title, max_value=200, color='green'):
    """Create a gauge chart for NPK values"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': max_value * 0.5},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.3], 'color': "lightgray"},
                {'range': [max_value * 0.3, max_value * 0.7], 'color': "lightblue"},
                {'range': [max_value * 0.7, max_value], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.8
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_history_chart(df):
    """Create time series chart for sensor history"""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['nitrogen'], name='N', 
                  line=dict(color='#1f77b4', width=2)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['phosphorus'], name='P',
                  line=dict(color='#ff7f0e', width=2)),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['potassium'], name='K',
                  line=dict(color='#2ca02c', width=2)),
        row=3, col=1
    )
    
    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="mg/kg", row=1, col=1)
    fig.update_yaxes(title_text="mg/kg", row=2, col=1)
    fig.update_yaxes(title_text="mg/kg", row=3, col=1)
    
    fig.update_layout(height=600, showlegend=False)
    return fig

def main():
    """Main dashboard"""
    
    # Header
    st.markdown('<p class="main-header">🌱 NPK Sensor Monitor Dashboard</p>', unsafe_allow_html=True)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        return
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/2E7D32/FFFFFF?text=NPK+Monitor", use_container_width=True)
        st.title("Settings")
        
        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
        
        # Sensor info
        st.subheader("Sensor Configuration")
        st.text(f"Port: {config['sensor']['port']}")
        st.text(f"Slave ID: {config['sensor']['slave_id']}")
        st.text(f"Baud Rate: {config['sensor']['baudrate']}")
        
        # ThingsBoard info
        st.subheader("ThingsBoard")
        st.text(f"Host: {config['thingsboard']['host']}")
        
    # Initialize components
    sensor = init_sensor(config)
    publisher = init_publisher(config)
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sensor_status = "🟢 Connected" if sensor else "🔴 Disconnected"
        st.metric("Sensor Status", sensor_status)
    
    with col2:
        if publisher:
            mqtt_connected = publisher.connect() if not publisher.is_connected() else publisher.is_connected()
            mqtt_status = "🟢 Connected" if mqtt_connected else "🔴 Disconnected"
        else:
            mqtt_status = "🔴 Disconnected"
        st.metric("MQTT Status", mqtt_status)
    
    with col3:
        st.metric("Device", config.get('device', {}).get('name', 'Unknown'))
    
    st.divider()
    
    # Read sensor data
    if sensor:
        try:
            data = sensor.read_all_sensors()
            
            # Current readings
            st.subheader("📊 Current Readings")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                n_value = data.get('nitrogen', 0) or 0
                fig_n = create_gauge_chart(n_value, "Nitrogen (N)", color='#1f77b4')
                st.plotly_chart(fig_n, use_container_width=True)
            
            with col2:
                p_value = data.get('phosphorus', 0) or 0
                fig_p = create_gauge_chart(p_value, "Phosphorus (P)", color='#ff7f0e')
                st.plotly_chart(fig_p, use_container_width=True)
            
            with col3:
                k_value = data.get('potassium', 0) or 0
                fig_k = create_gauge_chart(k_value, "Potassium (K)", color='#2ca02c')
                st.plotly_chart(fig_k, use_container_width=True)
            
            # Additional sensors
            if any(key in data for key in ['temperature', 'moisture', 'ph', 'ec']):
                st.subheader("🌡️ Additional Sensors")
                cols = st.columns(4)
                
                if 'temperature' in data and data['temperature'] is not None:
                    with cols[0]:
                        st.metric("Temperature", f"{data['temperature']:.1f} °C")
                
                if 'moisture' in data and data['moisture'] is not None:
                    with cols[1]:
                        st.metric("Moisture", f"{data['moisture']:.1f} %")
                
                if 'ph' in data and data['ph'] is not None:
                    with cols[2]:
                        st.metric("pH", f"{data['ph']:.1f}")
                
                if 'ec' in data and data['ec'] is not None:
                    with cols[3]:
                        st.metric("EC", f"{data['ec']:.0f} μS/cm")
            
            # Raw data
            with st.expander("🔍 Raw Data"):
                st.json(data)
            
            # Publish button
            if publisher and publisher.is_connected():
                if st.button("📤 Publish to ThingsBoard", type="primary"):
                    with st.spinner("Publishing..."):
                        if publisher.publish_telemetry(data):
                            st.success("Data published successfully!")
                        else:
                            st.error("Failed to publish data")
            
            # Simulated history (in production, use a database)
            st.subheader("📈 Historical Data (Last 24 Hours)")
            st.info("Note: This is simulated data. In production, implement data logging to display actual history.")
            
            # Generate sample data
            now = datetime.now()
            timestamps = [now - timedelta(hours=i) for i in range(24, 0, -1)]
            history_df = pd.DataFrame({
                'timestamp': timestamps,
                'nitrogen': [n_value + (i % 10) for i in range(24)],
                'phosphorus': [p_value + (i % 8) for i in range(24)],
                'potassium': [k_value + (i % 12) for i in range(24)]
            })
            
            fig_history = create_history_chart(history_df)
            st.plotly_chart(fig_history, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error reading sensor: {e}")
    else:
        st.error("Sensor not initialized. Check configuration and connection.")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == '__main__':
    main()
