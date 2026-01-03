"""Tests for the FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from ai_engine.api.server import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Decision Engine"
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_status_endpoint():
    """Test status endpoint."""
    response = client.get("/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"


def test_decide_endpoint():
    """Test decision endpoint."""
    request_data = {
        "symbol": "BTC/USD",
        "prices": [50000, 50100, 50200, 50300, 50250, 50400, 50500, 50450, 50600, 50700],
        "volumes": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500],
        "proposed_action": "buy",
        "proposed_size": 1000.0,
        "account_balance": 10000.0,
    }
    
    response = client.post("/ai/decide", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["symbol"] == "BTC/USD"
    assert "action" in data
    assert "confidence" in data
    assert "reasoning" in data
    assert data["action"] in ["buy", "sell", "hold"]


def test_decide_endpoint_validation():
    """Test decision endpoint with invalid data."""
    request_data = {
        "symbol": "BTC/USD",
        "prices": [],  # Empty prices should fail
        "volumes": [],
    }
    
    response = client.post("/ai/decide", json=request_data)
    assert response.status_code == 422  # Validation error
