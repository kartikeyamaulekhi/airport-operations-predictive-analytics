import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Model paths - relative to /app in Docker, relative to ml-service/ locally
    MODEL_PATH           = os.getenv("MODEL_PATH",           "saved_models/delay_model_v1.pkl")
    TRAFFIC_MODEL_PATH   = os.getenv("TRAFFIC_MODEL_PATH",   "saved_models/traffic_model_v1.pkl")
    DATA_PATH            = os.getenv("DATA_PATH",            "data/flight_delay_clean.csv")
    TRAFFIC_DATA_PATH    = os.getenv("TRAFFIC_DATA_PATH",    "data/airport_traffic_data.csv")
    DELAY_THRESHOLD      = float(os.getenv("DELAY_THRESHOLD", "0.20"))
    TRAFFIC_FORECAST_DAYS = int(os.getenv("TRAFFIC_FORECAST_DAYS", "30"))
    MODEL_VERSION        = os.getenv("MODEL_VERSION",        "v1")
    API_HOST             = os.getenv("API_HOST",             "0.0.0.0")
    API_PORT             = int(os.getenv("API_PORT",         "8000"))

print("[INFO] Configuration constants loaded cleanly.")
