# backend_api.py
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()
model = joblib.load("failure_model.tar.gz")

class SensorData(BaseModel):
    air_temp_K: float
    process_temp_K: float
    rotational_speed_rpm: int
    torque_Nm: float
    tool_wear_min: int
    type: str  # L, M, H

type_mapping = {"L": 0, "M": 1, "H": 2}

@app.post("/predict")
def predict(data: SensorData):
    try:
        input_data = [
            data.air_temp_K,
            data.process_temp_K,
            data.rotational_speed_rpm,
            data.torque_Nm,
            data.tool_wear_min,
            type_mapping[data.type]
        ]
        prediction = model.predict([input_data])[0]
        return {"failure_prediction": int(prediction)}
    except Exception as e:
        return {"error": str(e)}
