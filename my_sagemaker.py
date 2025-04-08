import sagemaker
from sagemaker.sklearn.model import SKLearnModel
import time

role = 'arn:aws:iam::198109037815:role/SageMakerExecutionRole'
model = SKLearnModel(
    entry_point="inference.py",       # Custom handler
    role=role,
    model_data="s3://5g-sensor-bucket/failure_model.tar.gz",
    framework_version="0.23-1",
    py_version="py3"
)

predictor = model.deploy(
    instance_type="ml.t2.medium",
    initial_instance_count=1,
    endpoint_name=f"predictive-maintenance-endpoint-{int(time.time())}"

)
