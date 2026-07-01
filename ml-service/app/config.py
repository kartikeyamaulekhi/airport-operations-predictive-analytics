"""
app/config.py
Centralised configuration — all file paths, thresholds, and API settings
loaded from environment variables with safe defaults.
Adding a new setting: just add an os.getenv() line here and reference it
anywhere via Config.SETTING_NAME. Never hardcode paths in other files.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Delay model ──────────────────────────────────────────────────────
    MODEL_PATH      = os.getenv("MODEL_PATH",      "saved_models/delay_model_v1.pkl")
    DATA_PATH       = os.getenv("DATA_PATH",       "data/flight_delay_clean.csv")
    DELAY_THRESHOLD = float(os.getenv("DELAY_THRESHOLD", 0.20))

    # ── Traffic forecasting model ─────────────────────────────────────────
    TRAFFIC_MODEL_PATH = os.getenv(
        "TRAFFIC_MODEL_PATH", "saved_models/traffic_model_v1.pkl"
    )
    TRAFFIC_DATA_PATH  = os.getenv(
        "TRAFFIC_DATA_PATH", "data/airport_traffic_data.csv"
    )
    TRAFFIC_FORECAST_DAYS = int(os.getenv("TRAFFIC_FORECAST_DAYS", 30))

    # ── Shared ────────────────────────────────────────────────────────────
    MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
    API_HOST      = os.getenv("API_HOST",      "127.0.0.1")
    API_PORT      = int(os.getenv("API_PORT",  8000))


print("[INFO] Configuration constants loaded cleanly.")
