import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.data import CANONICAL_TEAMS


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "version" in data
    assert set(data["available_classes"]) == set(CANONICAL_TEAMS)


def test_predict_endpoint_valid_request(client):
    payload = {
        "request_id": "SR510823",
        "channel": "chat",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
        "request_text": "water purifier leaking from bottom after technician visit",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "SR510823"
    assert data["predicted_team"] in CANONICAL_TEAMS
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0
    assert isinstance(data["review_recommended"], bool)


def test_predict_endpoint_minimal_request(client):
    payload = {
        "request_text": "where to buy spare jar for mixer grinder",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] == "Filters & Consumables"
    assert data["confidence"] > 0.50


def test_predict_endpoint_missing_text_validation_error(client):
    payload = {
        "channel": "chat",
        "product_family": "Water Purifier",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation)
