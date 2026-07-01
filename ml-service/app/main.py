from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
from app.config import Config

app = FastAPI(title="Airport Operations Predictive Analytics API", version="1.0.0")

if not os.path.exists(Config.MODEL_PATH):
    raise RuntimeError(f"Model artifact not found at {Config.MODEL_PATH}")

model = joblib.load(Config.MODEL_PATH)

class FlightFeatures(BaseModel):
    year: float
    month: float
    arr_flights: float
    is_summer: float
    is_winter_holiday: float
    years_since_2013: float
    airport_avg_delay_rate: float
    carrier_avg_delay_rate: float

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2026.0,
                "month": 7.0,
                "arr_flights": 150.0,
                "is_summer": 1.0,
                "is_winter_holiday": 0.0,
                "years_since_2013": 13.0,
                "airport_avg_delay_rate": 0.185,
                "carrier_avg_delay_rate": 0.142
            }
        }

@app.get("/")
def read_root():
    return {"status": "healthy", "model_version": "v1"}

@app.post("/predict")
def predict_delay(payload: FlightFeatures):
    try:
        input_dict = payload.model_dump()
        ordered_features = [input_dict[col] for col in [
            "year", "month", "arr_flights", "is_summer", 
            "is_winter_holiday", "years_since_2013", 
            "airport_avg_delay_rate", "carrier_avg_delay_rate"
        ]]
        
        input_data = np.array(ordered_features).reshape(1, -1)
        prediction = int(model.predict(input_data)[0])
        probability = float(model.predict_proba(input_data)[0][1])
        
        return {
            "high_delay_prediction": prediction,
            "high_delay_probability": round(probability, 4),
            "status": "disruption_risk" if prediction == 1 else "nominal"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)