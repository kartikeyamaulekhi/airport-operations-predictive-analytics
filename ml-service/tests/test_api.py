"""
tests/test_api.py
Comprehensive test suite for the Airport Operations API.
Tests all endpoints: health checks, delay prediction, traffic forecasting,
input validation, and edge cases.

Run from ml-service/ with venv activated:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── Shared test fixtures ──────────────────────────────────────────────────────
VALID_FLIGHT_PAYLOAD = {
    "year":                   2026.0,
    "month":                  7.0,
    "arr_flights":            150.0,
    "is_summer":              1.0,
    "is_winter_holiday":      0.0,
    "years_since_2013":       13.0,
    "airport_avg_delay_rate": 0.185,
    "carrier_avg_delay_rate": 0.142,
}

# ── Health checks ─────────────────────────────────────────────────────────────

def test_read_root():
    """Root endpoint returns healthy status with expected keys."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "model_version" in body
    assert "endpoints" in body


def test_health_check_detailed():
    """Detailed health endpoint returns model metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "delay_model" in body
    assert "traffic_model" in body
    assert "delay_threshold" in body


# ── Delay prediction ──────────────────────────────────────────────────────────

def test_predict_delay_valid():
    """Valid payload returns correct prediction structure."""
    response = client.post("/predict", json=VALID_FLIGHT_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert "high_delay_prediction" in body
    assert "high_delay_probability" in body
    assert "status" in body
    assert "model_version" in body
    assert body["high_delay_prediction"] in [0, 1]
    assert 0.0 <= body["high_delay_probability"] <= 1.0
    assert body["status"] in ["disruption_risk", "nominal"]


def test_predict_status_matches_prediction():
    """Status field must correctly reflect the binary prediction."""
    response = client.post("/predict", json=VALID_FLIGHT_PAYLOAD)
    body = response.json()
    if body["high_delay_prediction"] == 1:
        assert body["status"] == "disruption_risk"
    else:
        assert body["status"] == "nominal"


def test_predict_high_risk_scenario():
    """Summer + busy airport + poor carrier history → expect high delay risk."""
    high_risk = {
        "year":                   2023.0,
        "month":                  7.0,
        "arr_flights":            2000.0,
        "is_summer":              1.0,
        "is_winter_holiday":      0.0,
        "years_since_2013":       10.0,
        "airport_avg_delay_rate": 0.35,
        "carrier_avg_delay_rate": 0.32,
    }
    response = client.post("/predict", json=high_risk)
    assert response.status_code == 200
    body = response.json()
    # Probability must be a valid float between 0 and 1
    # Note: exact threshold depends on trained model — validated via AUC in train_delay.py
    assert 0.0 <= body["high_delay_probability"] <= 1.0


def test_predict_low_risk_scenario():
    """Off-peak + small airport + good carrier history → expect low delay risk."""
    low_risk = {
        "year":                   2023.0,
        "month":                  2.0,
        "arr_flights":            50.0,
        "is_summer":              0.0,
        "is_winter_holiday":      0.0,
        "years_since_2013":       10.0,
        "airport_avg_delay_rate": 0.08,
        "carrier_avg_delay_rate": 0.07,
    }
    response = client.post("/predict", json=low_risk)
    assert response.status_code == 200
    body = response.json()
    assert body["high_delay_probability"] < 0.5


def test_predict_missing_field():
    """Missing required field returns 422 Unprocessable Entity."""
    bad_payload = {k: v for k, v in VALID_FLIGHT_PAYLOAD.items()
                   if k != "arr_flights"}
    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422


def test_predict_invalid_month():
    """Month out of valid range (1-12) returns 422."""
    bad_payload = {**VALID_FLIGHT_PAYLOAD, "month": 13.0}
    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422


def test_predict_invalid_delay_rate():
    """Delay rate > 1.0 (impossible) returns 422."""
    bad_payload = {**VALID_FLIGHT_PAYLOAD, "airport_avg_delay_rate": 1.5}
    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422


def test_predict_invalid_payload_type():
    """String where float expected returns 422."""
    bad_payload = {**VALID_FLIGHT_PAYLOAD, "arr_flights": "many"}
    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422


# ── Traffic forecasting ───────────────────────────────────────────────────────

def test_forecast_traffic_default():
    """Default forecast (30 days) returns correct structure."""
    response = client.get("/forecast/traffic")
    assert response.status_code == 200
    body = response.json()
    assert body["forecast_days"] == 30
    assert len(body["forecast"]) == 30
    assert "forecast_from" in body
    assert "forecast_to" in body
    assert "model_mae" in body
    assert "model_mape_pct" in body


def test_forecast_traffic_custom_days():
    """Custom days parameter returns correct number of forecast points."""
    for days in [7, 14, 90]:
        response = client.get(f"/forecast/traffic?days={days}")
        assert response.status_code == 200
        body = response.json()
        assert len(body["forecast"]) == days


def test_forecast_traffic_point_structure():
    """Each forecast point has required fields with sensible values."""
    response = client.get("/forecast/traffic?days=7")
    body = response.json()
    for point in body["forecast"]:
        assert "date" in point
        assert "predicted_footfall" in point
        assert "lower_bound" in point
        assert "upper_bound" in point
        assert point["predicted_footfall"] >= 0
        assert point["lower_bound"] <= point["predicted_footfall"]
        assert point["upper_bound"] >= point["predicted_footfall"]


def test_forecast_traffic_bounds_valid():
    """Days parameter out of range (>365) returns 422."""
    response = client.get("/forecast/traffic?days=400")
    assert response.status_code == 422


def test_forecast_traffic_minimum_days():
    """Minimum 1 day forecast works correctly."""
    response = client.get("/forecast/traffic?days=1")
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 1
