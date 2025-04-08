# iot_data_sender.py
import requests
import random
import time
import json

URL = "http://localhost:8000/predict"  # Replace with actual endpoint later

def generate_sensor_data():
    return {
        "air_temp_K": round(random.uniform(290, 310), 2),
        "process_temp_K": round(random.uniform(300, 320), 2),
        "rotational_speed_rpm": random.randint(1200, 1600),
        "torque_Nm": round(random.uniform(20, 50), 2),
        "tool_wear_min": random.randint(0, 250),
        "type": random.choice(["L", "M", "H"])
    }

while True:
    data = generate_sensor_data()
    print(f"Sending: {data}")
    try:
        res = requests.post(URL, json=data)
        print(f"Response: {res.json()}")
    except Exception as e:
        print("Failed to send:", e)
    time.sleep(2)  # simulate 1 reading every 2 seconds
