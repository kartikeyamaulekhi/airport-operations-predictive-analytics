import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    MODEL_VERSION = "v1"
    MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "delay_model_v1.pkl")
    TRAFFIC_MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "traffic_model_v1.pkl")
    DELAY_THRESHOLD = 0.5
    API_HOST = "0.0.0.0"
    API_PORT = 8000
