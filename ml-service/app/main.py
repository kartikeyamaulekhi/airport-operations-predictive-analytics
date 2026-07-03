from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import Config
from app.services import ml_service

app = FastAPI(title="Airport Operations Predictive Analytics API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class FlightFeatures(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2026.0, "month": 7.0, "arr_flights": 150.0, 
                "is_summer": 1.0, "is_winter_holiday": 0.0, "years_since_2013": 13.0, 
                "airport_avg_delay_rate": 0.185, "carrier_avg_delay_rate": 0.142
            }
        }
    }
    year: float = Field(..., ge=2013, le=2030)
    month: float = Field(..., ge=1, le=12)
    arr_flights: float = Field(..., ge=1)
    is_summer: float = Field(..., ge=0, le=1)
    is_winter_holiday: float = Field(..., ge=0, le=1)
    years_since_2013: float = Field(..., ge=0)
    airport_avg_delay_rate: float = Field(..., ge=0, le=1)
    carrier_avg_delay_rate: float = Field(..., ge=0, le=1)

class DelayPredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    high_delay_prediction: int
    high_delay_probability: float
    status: str
    model_version: str

class TrafficForecastPoint(BaseModel):
    date: str
    predicted_footfall: int
    lower_bound: int
    upper_bound: int

class TrafficForecastResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    forecast_days: int
    forecast_from: str
    forecast_to: str
    model_mae: float
    model_mape_pct: float
    forecast: list[TrafficForecastPoint]

@app.get("/", tags=["Health"])
def read_root():
    return {
        "status": "healthy", 
        "model_version": Config.MODEL_VERSION, 
        "endpoints": {"delay_prediction": "POST /predict", "traffic_forecast": "GET /forecast/traffic", "api_docs": "GET /docs"}
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy", 
        "model_version": Config.MODEL_VERSION, 
        "delay_model": Config.MODEL_PATH, 
        "traffic_model": Config.TRAFFIC_MODEL_PATH, 
        "traffic_model_mae": ml_service.traffic_meta.get("mae"), 
        "traffic_model_mape_pct": ml_service.traffic_meta.get("mape_pct"), 
        "delay_threshold": Config.DELAY_THRESHOLD
    }

@app.post("/predict", response_model=DelayPredictionResponse, tags=["Delay Prediction"])
def predict_delay(payload: FlightFeatures):
    try:
        input_dict = payload.model_dump()
        prediction, probability = ml_service.predict_flight_delay(input_dict)
        
        return DelayPredictionResponse(
            high_delay_prediction=prediction,
            high_delay_probability=round(probability, 4),
            status="disruption_risk" if prediction == 1 else "nominal",
            model_version=Config.MODEL_VERSION
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing feature mapping: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal inference failure: {str(e)}")

@app.get("/forecast/traffic", response_model=TrafficForecastResponse, tags=["Traffic Forecasting"])
def forecast_traffic(days: int = Query(default=30, ge=1, le=365)):
    try:
        points = ml_service.run_traffic_forecast(days)
        return TrafficForecastResponse(
            forecast_days=days,
            forecast_from=points[0]["date"],
            forecast_to=points[-1]["date"],
            model_mae=ml_service.traffic_meta.get("mae", 0.0),
            model_mape_pct=ml_service.traffic_meta.get("mape_pct", 0.0),
            forecast=points
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting engine failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)

import os
import uvicorn
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run('app.main:app', host='0.0.0.0', port=port)
