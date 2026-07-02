import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_traffic_forecast_endpoint_valid():
    response = client.get("/forecast/traffic?days=3")
    assert response.status_code == 200
    data = response.json()
    
    # Updated keys to use the native snake_case defined in your Pydantic models
    assert data["forecast_days"] == 3
    assert "forecast_from" in data
    assert "forecast_to" in data
    assert isinstance(data["forecast"], list)

def test_traffic_forecast_endpoint_invalid_params():
    response = client.get("/forecast/traffic?days=not-a-number")
    assert response.status_code == 422
