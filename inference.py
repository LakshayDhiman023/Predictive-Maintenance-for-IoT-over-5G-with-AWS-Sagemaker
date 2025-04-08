# inference.py

import joblib
import json
import os
import numpy as np

# Called when the SageMaker model is initialized
def model_fn(model_dir):
    """Load the model from the model directory"""
    model_path = os.path.join(model_dir, "failure_model.tar.gz")
    model = joblib.load(model_path)
    return model

# Called when a request is received
def input_fn(request_body, request_content_type):
    """Parse input data from JSON to numpy array"""
    if request_content_type == "application/json":
        data = json.loads(request_body)

        # Map type string to encoded int
        type_mapping = {"L": 0, "M": 1, "H": 2}
        data["type"] = type_mapping.get(data["type"], 1)  # default to 'M' if unknown

        # Construct feature array
        features = [
            data["air_temp_K"],
            data["process_temp_K"],
            data["rotational_speed_rpm"],
            data["torque_Nm"],
            data["tool_wear_min"],
            data["type"]
        ]
        return np.array([features])
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

# Called to make prediction
def predict_fn(input_data, model):
    """Perform prediction"""
    prediction = model.predict(input_data)
    return int(prediction[0])

# Called to format output
def output_fn(prediction, response_content_type):
    """Return prediction as JSON"""
    if response_content_type == "application/json":
        return json.dumps({"failure_prediction": prediction})
    else:
        raise ValueError(f"Unsupported response content type: {response_content_type}")
