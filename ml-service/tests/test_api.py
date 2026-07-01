import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "model_version": "v1"}

def test_predict_delay_endpoint():
    # Sample payload matching our Pydantic schema
    payload = {
        "year": 2026.0,
        "month": 7.0,
        "arr_flights": 150.0,
        "is_summer": 1.0,
        "is_winter_holiday": 0.0,
        "years_since_2013": 13.0,
        "airport_avg_delay_rate": 0.185,
        "carrier_avg_delay_rate": 0.142
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "high_delay_prediction" in data
    assert "high_delay_probability" in data
    assert "status" in data
    assert data["status"] in ["disruption_risk", "nominal"]

def test_invalid_payload():
    # Missing required fields to verify validation layer catches bad data
    bad_payload = {"year": 2026.0}
    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422  # FastAPI Unprocessable Entity