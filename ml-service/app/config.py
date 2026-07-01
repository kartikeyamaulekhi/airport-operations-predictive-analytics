import os
from dotenv import load_dotenv

# Load the .env file if it exists
load_dotenv()

class Config:
    MODEL_PATH = os.getenv("MODEL_PATH", "saved_models/delay_model_v1.pkl")
    DATA_PATH = os.getenv("DATA_PATH", "data/flight_delay_clean.csv")
    DELAY_THRESHOLD = float(os.getenv("DELAY_THRESHOLD", 0.20))
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", 8000))

print("[INFO] Configuration constants loaded cleanly.")