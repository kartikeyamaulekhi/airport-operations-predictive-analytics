import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Render container path vs Local machine path fallback
if os.path.exists("/app/ml-service/saved_models"):
    RENDER_ROOT = "/app/ml-service"
elif os.path.exists("/app/saved_models"):
    RENDER_ROOT = "/app"
else:
    RENDER_ROOT = str(BASE_DIR)

class Config:
    MODEL_VERSION = "v1"
    MODEL_PATH = os.path.join(RENDER_ROOT, "saved_models", "delay_model_v1.pkl")
    TRAFFIC_MODEL_PATH = os.path.join(RENDER_ROOT, "saved_models", "traffic_model_v1.pkl")
    DELAY_THRESHOLD = 0.5
    API_HOST = "0.0.0.0"
    API_PORT = 8000
