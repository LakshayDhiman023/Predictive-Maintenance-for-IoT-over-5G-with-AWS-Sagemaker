# dashboard.py

import streamlit as st
import requests
import random
import pandas as pd

# -----------------------
# Helper: Generate Fake Data
# -----------------------
def generate_fake_sensor_data():
    return {
        "air_temp_K": round(random.uniform(290, 310), 2),
        "process_temp_K": round(random.uniform(300, 320), 2),
        "rotational_speed_rpm": random.randint(1200, 1600),
        "torque_Nm": round(random.uniform(20, 50), 2),
        "tool_wear_min": random.randint(0, 250),
        "type": random.choice(["L", "M", "H"])
    }

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Predictive Maintenance Dashboard", layout="centered")
st.title("🔧 IoT Predictive Maintenance Dashboard")

endpoint = "http://localhost:8000/predict"  # Replace with SageMaker endpoint if needed

# Store previous data in session
if "history" not in st.session_state:
    st.session_state.history = []

if st.button("🚀 Send Fake Sensor Data"):
    fake_data = generate_fake_sensor_data()
    st.write("📡 Sent Sensor Data:")
    st.json(fake_data)

    try:
        response = requests.post(endpoint, json=fake_data)
        prediction = response.json().get("failure_prediction", "Unknown")
        st.success(f"⚙️ Prediction: {'❌ Failure' if prediction else '✅ Safe'}")

        # Append to session history
        st.session_state.history.append({**fake_data, "prediction": prediction})
    except Exception as e:
        st.error(f"Failed to get prediction: {e}")

# -----------------------
# Display History Table
# -----------------------
if st.session_state.history:
    st.subheader("📊 Previous Readings")
    history_df = pd.DataFrame(st.session_state.history)
    history_df["prediction"] = history_df["prediction"].map({0: "Safe", 1: "Failure"})
    st.dataframe(history_df[::-1], use_container_width=True)
