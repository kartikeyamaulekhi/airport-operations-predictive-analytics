"""
app/main.py
Airport Operations Predictive Analytics — FastAPI Service
Exposes two ML endpoints:
  POST /predict          → XGBoost delay risk prediction
  GET  /forecast/traffic → Prophet passenger footfall forecast

Design principles:
  - All config from Config class (no hardcoded paths)
  - Pydantic schemas enforce strict input typing
  - Models loaded once at startup (not per-request) for performance
  - Graceful error handling with meaningful HTTP status codes
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import Config

# ── App initialisation ────────────────────────────────────────────────────────
app = FastAPI(
    title="Airport Operations Predictive Analytics API",
    description=(
        "Predicts flight delay risk and forecasts passenger traffic "
        "using real US DOT/BTS data (2013-2023). "
        "Built during internship at Lucknow International Airport (Adani Group)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allows the React dashboard (any origin in dev, lock down in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Model loading (once at startup) ──────────────────────────────────────────
if not os.path.exists(Config.MODEL_PATH):
    raise RuntimeError(f"Delay model not found at {Config.MODEL_PATH}. "
                       f"Run: python ml/train_delay.py")
delay_model = joblib.load(Config.MODEL_PATH)

if not os.path.exists(Config.TRAFFIC_MODEL_PATH):
    raise RuntimeError(f"Traffic model not found at {Config.TRAFFIC_MODEL_PATH}. "
                       f"Run: python ml/train_traffic.py")
traffic_model = joblib.load(Config.TRAFFIC_MODEL_PATH)

# Load traffic model metadata (MAE, MAPE etc.) for /health response
_traffic_meta_path = Config.TRAFFIC_MODEL_PATH.replace(".pkl", "_meta.json")
traffic_meta = {}
if os.path.exists(_traffic_meta_path):
    with open(_traffic_meta_path) as f:
        traffic_meta = json.load(f)

print("[INFO] All models loaded successfully.")

# ── Pydantic schemas ──────────────────────────────────────────────────────────
FEATURE_ORDER = [
    "year", "month", "arr_flights", "is_summer",
    "is_winter_holiday", "years_since_2013",
    "airport_avg_delay_rate", "carrier_avg_delay_rate",
]


class FlightFeatures(BaseModel):
    year:                  float = Field(..., ge=2013, le=2030,
                                         description="Calendar year")
    month:                 float = Field(..., ge=1,    le=12,
                                         description="Calendar month (1-12)")
    arr_flights:           float = Field(..., ge=1,
                                         description="Total arriving flights this month")
    is_summer:             float = Field(..., ge=0, le=1,
                                         description="1 if June/July/August else 0")
    is_winter_holiday:     float = Field(..., ge=0, le=1,
                                         description="1 if December/January else 0")
    years_since_2013:      float = Field(..., ge=0,
                                         description="year minus 2013")
    airport_avg_delay_rate: float = Field(..., ge=0, le=1,
                                          description="Historical avg delay rate for this airport")
    carrier_avg_delay_rate: float = Field(..., ge=0, le=1,
                                          description="Historical avg delay rate for this carrier")

    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2026.0,
                "month": 7.0,
                "arr_flights": 150.0,
                "is_summer": 1.0,
                "is_winter_holiday": 0.0,
                "years_since_2013": 13.0,
                "airport_avg_delay_rate": 0.185,
                "carrier_avg_delay_rate": 0.142,
            }
        }
    }


class DelayPredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}


class TrafficForecastPoint(BaseModel):
    date:            str
    predicted_footfall:      int
    lower_bound:     int
    upper_bound:     int


class TrafficForecastResponse(BaseModel):
    model_config = {"protected_namespaces": ()}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def read_root():
    """Basic health check — confirms both models are loaded."""
    return {
        "status":        "healthy",
        "model_version": Config.MODEL_VERSION,
        "endpoints": {
            "delay_prediction":    "POST /predict",
            "traffic_forecast":    "GET  /forecast/traffic",
            "api_docs":            "GET  /docs",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check including model metadata."""
    return {
        "status":          "healthy",
        "model_version":   Config.MODEL_VERSION,
        "delay_model":     Config.MODEL_PATH,
        "traffic_model":   Config.TRAFFIC_MODEL_PATH,
        "traffic_model_mae":      traffic_meta.get("mae"),
        "traffic_model_mape_pct": traffic_meta.get("mape_pct"),
        "delay_threshold": Config.DELAY_THRESHOLD,
    }


@app.post("/predict", response_model=DelayPredictionResponse, tags=["Delay Prediction"])
def predict_delay(payload: FlightFeatures):
    """
    Predict whether a carrier-airport-month combination will have a HIGH
    delay rate (>20% of flights delayed 15+ minutes).

    Returns:
    - high_delay_prediction: 1 = high delay risk, 0 = nominal
    - high_delay_probability: model confidence (0.0 – 1.0)
    - status: 'disruption_risk' or 'nominal'
    """
    try:
        input_dict  = payload.model_dump()
        features    = np.array(
            [input_dict[col] for col in FEATURE_ORDER]
        ).reshape(1, -1)

        prediction  = int(delay_model.predict(features)[0])
        probability = float(delay_model.predict_proba(features)[0][1])

        return DelayPredictionResponse(
            high_delay_prediction=prediction,
            high_delay_probability=round(probability, 4),
            status="disruption_risk" if prediction == 1 else "nominal",
            model_version=Config.MODEL_VERSION,
        )
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail=f"Inference failed: {str(e)}")


@app.get("/forecast/traffic",
         response_model=TrafficForecastResponse,
         tags=["Traffic Forecasting"])
def forecast_traffic(
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to forecast (1–365)",
    )
):
    """
    Forecast daily airport passenger footfall for the next N days using
    a Prophet time-series model trained on 6 years of historical data.

    Returns daily predictions with 95% confidence intervals — useful for
    staff scheduling, gate allocation, and resource planning.
    """
    try:
        future    = traffic_model.make_future_dataframe(periods=days, freq="D")
        forecast  = traffic_model.predict(future)
        result_df = forecast.tail(days)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

        points = [
            TrafficForecastPoint(
                date=str(row["ds"].date()),
                predicted_footfall=max(0, int(round(row["yhat"]))),
                lower_bound=max(0, int(round(row["yhat_lower"]))),
                upper_bound=max(0, int(round(row["yhat_upper"]))),
            )
            for _, row in result_df.iterrows()
        ]

        return TrafficForecastResponse(
            forecast_days=days,
            forecast_from=points[0].date,
            forecast_to=points[-1].date,
            model_mae=traffic_meta.get("mae", 0.0),
            model_mape_pct=traffic_meta.get("mape_pct", 0.0),
            forecast=points,
        )
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Forecasting failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
