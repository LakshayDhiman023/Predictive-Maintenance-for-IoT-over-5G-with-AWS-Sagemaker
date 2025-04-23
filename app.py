import streamlit as st
import serial
import json
import boto3
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'arduino' not in st.session_state:
    st.session_state.arduino = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = False
if 'latency_history' not in st.session_state:
    st.session_state.latency_history = []

# AWS SageMaker endpoint configuration
ENDPOINT_NAME = 'cpu-state-xgboost-endpoint-improved-1744570066'
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')

# Arduino Configuration
ARDUINO_PORT = 'COM13'
BAUD_RATE = 9600
TIMEOUT = 1

# Streamlit app title
st.set_page_config(page_title="CPU State Monitor", layout="wide")
st.title("CPU State Monitor")

def connect_arduino():
    """Establish connection to Arduino"""
    try:
        if st.session_state.arduino is None:
            st.session_state.arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=TIMEOUT)
            st.session_state.connection_status = True
            return True
    except Exception as e:
        st.error(f"Failed to connect to Arduino: {str(e)}")
        st.session_state.connection_status = False
        st.session_state.arduino = None
        return False

def disconnect_arduino():
    """Safely disconnect from Arduino"""
    try:
        if st.session_state.arduino is not None:
            st.session_state.arduino.close()
            st.session_state.arduino = None
            st.session_state.connection_status = False
            st.success("Arduino disconnected successfully")
    except Exception as e:
        st.error(f"Error disconnecting Arduino: {str(e)}")

def read_sensor_data():
    """Read data from Arduino and return parsed values"""
    try:
        if st.session_state.arduino is None:
            if not connect_arduino():
                return None
        
        # Read data from Arduino
        line = st.session_state.arduino.readline().decode('utf-8').strip()
        
        # Parse the data
        data = {}
        parts = line.split(" | ")
        
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                key = key.strip().lower()
                try:
                    value = float(value.split()[0])  # Extract the numeric value
                    
                    # Map the keys to the expected format
                    if "temperature" in key:
                        data['temperature'] = value
                    elif "voltage" in key:
                        data['voltage'] = value
                    elif "current" in key:
                        data['current'] = value
                    elif "cpu usage" in key or "cpu" in key:
                        data['cpu_usage'] = value
                    elif "fan speed" in key or "fan" in key:
                        data['fan_speed'] = value
                except ValueError:
                    continue
        
        return data
    except Exception as e:
        st.error(f"Error reading sensor data: {str(e)}")
        # If there's an error, try to reconnect
        st.session_state.arduino = None
        st.session_state.connection_status = False
        return None

def get_sensor_state(sensor_type, value):
    """Determine sensor state based on thresholds"""
    ranges = {
        'temperature': {'normal': (0, 70), 'warning': (70, 85)},
        'voltage': {'normal': (3.0, 3.6), 'warning': (2.7, 3.0)},
        'current': {'normal': (0, 2.0), 'warning': (2.0, 2.5)},
        'cpu_usage': {'normal': (0, 70), 'warning': (70, 85)},
        'fan_speed': {'normal': (1000, 2500), 'warning': (2500, 3000)}
    }
    
    range_values = ranges[sensor_type]
    if range_values['normal'][0] <= value <= range_values['normal'][1]:
        return 0  # Normal
    elif range_values['warning'][0] <= value <= range_values['warning'][1]:
        return 1  # Warning
    else:
        return 2  # Critical

def get_prediction(data):
    """Get prediction from SageMaker endpoint"""
    try:
        # Add state labels
        features = [
            data['temperature'],
            data['voltage'],
            data['current'],
            data['cpu_usage'],
            data['fan_speed'],
            get_sensor_state('temperature', data['temperature']),
            get_sensor_state('voltage', data['voltage']),
            get_sensor_state('current', data['current']),
            get_sensor_state('cpu_usage', data['cpu_usage']),
            get_sensor_state('fan_speed', data['fan_speed'])
        ]
        
        # Convert to CSV
        csv_data = ','.join(map(str, features))
        
        # Record start time
        start_time = time.time()
        
        # Get prediction
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',
            Body=csv_data
        )
        
        # Calculate latency
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Parse response
        result = response['Body'].read().decode().strip()
        probabilities = [float(p) for p in result.split(',')]
        
        # Store latency information
        network_type = st.session_state.get('network_type', '4G')  # Default to 4G if not set
        st.session_state.latency_history.append({
            'timestamp': datetime.now().isoformat(),
            'network_type': network_type,
            'latency': latency,
            'prediction': ['Normal', 'Warning', 'Critical'][probabilities.index(max(probabilities))]
        })
        
        return {
            'input_data': csv_data,
            'probabilities': {
                'Normal': probabilities[0],
                'Warning': probabilities[1],
                'Critical': probabilities[2]
            },
            'prediction': ['Normal', 'Warning', 'Critical'][probabilities.index(max(probabilities))],
            'latency': latency
        }
    except Exception as e:
        st.error(f"Error getting prediction: {str(e)}")
        return None

# Create tabs
data_tab, history_tab, latency_tab = st.tabs(["Current Data", "History", "Network Latency"])

# Network type selector in sidebar
with st.sidebar:
    st.subheader("Network Configuration")
    network_type = st.radio(
        "Select Network Type",
        options=['4G', '5G'],
        key='network_type'
    )

# Connection status and control in sidebar
with st.sidebar:
    st.subheader("Arduino Connection")
    status_color = "green" if st.session_state.connection_status else "red"
    st.markdown(f"Status: <span style='color: {status_color}'>{'Connected' if st.session_state.connection_status else 'Disconnected'}</span>", unsafe_allow_html=True)
    
    if not st.session_state.connection_status:
        if st.button("Connect to Arduino"):
            connect_arduino()
            st.rerun()
    else:
        if st.button("Disconnect Arduino"):
            disconnect_arduino()
            st.rerun()

# Current Data Tab
with data_tab:
    read_button = st.button("Read Sensor Data and Predict", disabled=not st.session_state.connection_status)
    
    if read_button:
        # Read sensor data
        sensor_data = read_sensor_data()
        
        if sensor_data and all(k in sensor_data for k in ['temperature', 'voltage', 'current', 'cpu_usage', 'fan_speed']):
            # Get prediction
            result = get_prediction(sensor_data)
            
            if result:
                # Store in history
                history_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'sensor_data': sensor_data,
                    'endpoint_input': result['input_data'],
                    'prediction': result['prediction'],
                    'probabilities': result['probabilities']
                }
                st.session_state.history.append(history_entry)
                
                # Display current data
                st.subheader("Sensor Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Raw Values")
                    for name, value in sensor_data.items():
                        st.write(f"{name.replace('_', ' ').title()}: {value:.2f}")
                
                with col2:
                    st.markdown("##### State Labels")
                    for name, value in sensor_data.items():
                        state = get_sensor_state(name, value)
                        state_name = {0: "Normal", 1: "Warning", 2: "Critical"}[state]
                        st.write(f"{name.replace('_', ' ').title()}: {state_name}")
                
                # Show endpoint input
                st.subheader("Data Sent to Endpoint")
                st.code(result['input_data'])
                
                # Show prediction
                st.subheader("Prediction Result")
                state_color = {
                    'Normal': 'green',
                    'Warning': 'orange',
                    'Critical': 'red'
                }[result['prediction']]
                
                st.markdown(f"""
                <h3 style='text-align: center'>
                    System Status: <span style='color: {state_color}'>{result['prediction']}</span>
                </h3>
                """, unsafe_allow_html=True)
                
                # Show probabilities
                st.subheader("State Probabilities")
                for state, prob in result['probabilities'].items():
                    color = {'Normal': 'green', 'Warning': 'orange', 'Critical': 'red'}[state]
                    st.markdown(f"**{state}**")
                    st.progress(float(prob))
                    st.markdown(f"<p style='text-align: right; color: {color}'>{prob:.1%}</p>", unsafe_allow_html=True)

# History Tab
with history_tab:
    st.header("Prediction History")
    
    if st.session_state.history:
        # Convert history to DataFrame
        history_df = pd.DataFrame(st.session_state.history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        # Time range selector
        st.subheader("Time Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=history_df['timestamp'].min().date(),
                min_value=history_df['timestamp'].min().date(),
                max_value=history_df['timestamp'].max().date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=history_df['timestamp'].max().date(),
                min_value=history_df['timestamp'].min().date(),
                max_value=history_df['timestamp'].max().date()
            )
        
        # Filter data based on selected date range
        mask = (history_df['timestamp'].dt.date >= start_date) & (history_df['timestamp'].dt.date <= end_date)
        filtered_df = history_df[mask]
        
        if not filtered_df.empty:
            # 1. State Probabilities Over Time
            st.subheader("System State Probabilities")
            fig_probs = go.Figure()
            
            for state in ['Normal', 'Warning', 'Critical']:
                probs = [entry['probabilities'][state] for entry in filtered_df.to_dict('records')]
                fig_probs.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=probs,
                    name=state,
                    fill='tonexty',
                    line=dict(
                        width=2,
                        color={'Normal': 'green', 'Warning': 'orange', 'Critical': 'red'}[state]
                    )
                ))
            
            fig_probs.update_layout(
                title="State Probabilities Over Time",
                xaxis_title="Time",
                yaxis_title="Probability",
                height=400,
                yaxis=dict(range=[0, 1]),
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            st.plotly_chart(fig_probs, use_container_width=True)
            
            # 2. Sensor Data Visualization
            st.subheader("Sensor Readings")
            
            # Create sensor data DataFrame
            sensor_data = pd.DataFrame([h['sensor_data'] for h in filtered_df.to_dict('records')])
            sensor_data.index = filtered_df['timestamp']
            
            # Sensor selection
            selected_sensors = st.multiselect(
                "Select sensors to display",
                ['temperature', 'voltage', 'current', 'cpu_usage', 'fan_speed'],
                default=['temperature', 'cpu_usage']
            )
            
            if selected_sensors:
                # Create subplots for selected sensors
                fig_sensors = make_subplots(
                    rows=len(selected_sensors),
                    cols=1,
                    subplot_titles=[s.replace('_', ' ').title() for s in selected_sensors],
                    vertical_spacing=0.05
                )
                
                # Add traces for each selected sensor
                for i, sensor in enumerate(selected_sensors, 1):
                    fig_sensors.add_trace(
                        go.Scatter(
                            x=sensor_data.index,
                            y=sensor_data[sensor],
                            name=sensor.replace('_', ' ').title(),
                            line=dict(width=2),
                            fill='tozeroy'
                        ),
                        row=i,
                        col=1
                    )
                    
                    # Add threshold lines
                    if sensor == 'temperature':
                        fig_sensors.add_hline(y=70, line_dash="dash", line_color="orange", row=i, col=1)
                        fig_sensors.add_hline(y=85, line_dash="dash", line_color="red", row=i, col=1)
                    elif sensor == 'voltage':
                        fig_sensors.add_hline(y=3.0, line_dash="dash", line_color="orange", row=i, col=1)
                        fig_sensors.add_hline(y=2.7, line_dash="dash", line_color="red", row=i, col=1)
                    elif sensor == 'current':
                        fig_sensors.add_hline(y=2.0, line_dash="dash", line_color="orange", row=i, col=1)
                        fig_sensors.add_hline(y=2.5, line_dash="dash", line_color="red", row=i, col=1)
                    elif sensor == 'cpu_usage':
                        fig_sensors.add_hline(y=70, line_dash="dash", line_color="orange", row=i, col=1)
                        fig_sensors.add_hline(y=85, line_dash="dash", line_color="red", row=i, col=1)
                    elif sensor == 'fan_speed':
                        fig_sensors.add_hline(y=2500, line_dash="dash", line_color="orange", row=i, col=1)
                        fig_sensors.add_hline(y=3000, line_dash="dash", line_color="red", row=i, col=1)
                
                fig_sensors.update_layout(
                    height=250 * len(selected_sensors),
                    showlegend=False,
                    hovermode='x unified'
                )
                st.plotly_chart(fig_sensors, use_container_width=True)
            
            # 3. State Distribution Pie Chart
            st.subheader("State Distribution")
            predictions = filtered_df['prediction'].value_counts()
            fig_pie = go.Figure(data=[go.Pie(
                labels=predictions.index,
                values=predictions.values,
                marker=dict(colors=['green', 'orange', 'red'])
            )])
            fig_pie.update_layout(
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # 4. Export functionality
            st.subheader("Export Data")
            if st.button("Download History Data as CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Click to Download",
                    data=csv,
                    file_name="sensor_history.csv",
                    mime="text/csv"
                )
    else:
        st.info("No history data available. Click 'Read Sensor Data and Predict' to collect data.")

# Latency Tab
with latency_tab:
    st.header("Network Latency Comparison")
    
    if st.session_state.latency_history:
        latency_df = pd.DataFrame(st.session_state.latency_history)
        latency_df['timestamp'] = pd.to_datetime(latency_df['timestamp'])
        
        # 1. Box Plot Comparison
        st.subheader("Latency Distribution by Network Type")
        fig_box = go.Figure()
        
        for network in ['4G', '5G']:
            network_data = latency_df[latency_df['network_type'] == network]['latency']
            if not network_data.empty:
                fig_box.add_trace(go.Box(
                    y=network_data,
                    name=network,
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ))
        
        fig_box.update_layout(
            title="Prediction Latency Distribution",
            yaxis_title="Latency (ms)",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        # 2. Time Series Comparison
        st.subheader("Latency Over Time")
        fig_time = go.Figure()
        
        for network in ['4G', '5G']:
            network_df = latency_df[latency_df['network_type'] == network]
            if not network_df.empty:
                fig_time.add_trace(go.Scatter(
                    x=network_df['timestamp'],
                    y=network_df['latency'],
                    name=network,
                    mode='lines+markers'
                ))
        
        fig_time.update_layout(
            title="Prediction Latency Trends",
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_time, use_container_width=True)
        
        # 3. Summary Statistics
        st.subheader("Latency Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 4G Network")
            g4_stats = latency_df[latency_df['network_type'] == '4G']['latency'].describe()
            if not g4_stats.empty:
                st.write(f"Average: {g4_stats['mean']:.2f} ms")
                st.write(f"Minimum: {g4_stats['min']:.2f} ms")
                st.write(f"Maximum: {g4_stats['max']:.2f} ms")
                st.write(f"Std Dev: {g4_stats['std']:.2f} ms")
        
        with col2:
            st.markdown("#### 5G Network")
            g5_stats = latency_df[latency_df['network_type'] == '5G']['latency'].describe()
            if not g5_stats.empty:
                st.write(f"Average: {g5_stats['mean']:.2f} ms")
                st.write(f"Minimum: {g5_stats['min']:.2f} ms")
                st.write(f"Maximum: {g5_stats['max']:.2f} ms")
                st.write(f"Std Dev: {g5_stats['std']:.2f} ms")
        
        # 4. Latency Improvement Analysis
        if not g4_stats.empty and not g5_stats.empty:
            st.subheader("5G Performance Improvement")
            improvement = ((g4_stats['mean'] - g5_stats['mean']) / g4_stats['mean']) * 100
            st.markdown(f"#### Average Latency Improvement: {improvement:.1f}%")
            
            # Create a gauge chart for improvement visualization
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=improvement,
                title={'text': "Latency Improvement with 5G"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "darkgray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': improvement
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # 5. Export Latency Data
        st.subheader("Export Latency Data")
        if st.button("Download Latency Data as CSV"):
            csv = latency_df.to_csv(index=False)
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name="latency_comparison.csv",
                mime="text/csv"
            )
    else:
        st.info("No latency data available. Make predictions with both 4G and 5G networks to see comparison.") 