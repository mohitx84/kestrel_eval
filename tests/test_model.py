import pytest
from src.data import CANONICAL_TEAMS
from src.predict import KestrelPredictor


@pytest.fixture(scope="module")
def predictor():
    return KestrelPredictor()


def test_predictor_loaded(predictor):
    assert predictor is not None
    assert len(predictor.classes_) == 7
    assert set(predictor.classes_) == set(CANONICAL_TEAMS)


def test_predict_one_structure(predictor):
    req = {
        "request_id": "TEST_001",
        "request_text": "display of air fryer gone blank please send technician",
        "channel": "chat",
        "product_family": "Air Fryer",
        "warranty_status": "in_warranty",
    }
    res = predictor.predict_one(req)
    assert "request_id" in res
    assert res["request_id"] == "TEST_001"
    assert "predicted_team" in res
    assert res["predicted_team"] in CANONICAL_TEAMS
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert "reasons" in res
    assert isinstance(res["reasons"], list)
    assert len(res["reasons"]) > 0
    assert "review_recommended" in res
    assert isinstance(res["review_recommended"], bool)
    assert "runner_up_team" in res
    assert "runner_up_confidence" in res


def test_edge_case_empty_text(predictor):
    req = {
        "request_id": "TEST_EMPTY",
        "request_text": "   ",
        "channel": "chat",
        "product_family": "Ceiling Fan",
        "warranty_status": "in_warranty",
    }
    res = predictor.predict_one(req)
    assert res["predicted_team"] in CANONICAL_TEAMS
    assert res["review_recommended"] is True
    assert any("empty" in r.lower() for r in res["reasons"])


def test_edge_case_corrupted_text(predictor):
    req = {
        "request_id": "TEST_CORRUPT",
        "request_text": "urgént: installer did not turn up for room heater asap â€¦",
        "channel": "ivr",
        "product_family": "Room Heater",
        "warranty_status": "in_warranty",
    }
    res = predictor.predict_one(req)
    assert res["predicted_team"] == "Installs & Demo"
    assert res["confidence"] > 0.50


def test_edge_case_missing_optional_fields(predictor):
    req = {
        "request_text": "need invoice copy for accounting",
    }
    res = predictor.predict_one(req)
    assert res["predicted_team"] == "Billing"
    assert res["confidence"] > 0.60


def test_edge_case_payment_for_installation_policy(predictor):
    # Customer mentions payment alongside installation
    req = {
        "request_id": "TEST_PAY_INSTALL",
        "request_text": "i paid online for installation but technician did not arrive for fan",
        "channel": "chat",
        "product_family": "Ceiling Fan",
        "warranty_status": "in_warranty",
    }
    res = predictor.predict_one(req)
    # Regardless of which queue is selected, the policy advisory reason must trigger
    assert any("Policy §3" in r for r in res["reasons"])
    # If routed to Billing, it must recommend human review
    if res["predicted_team"] == "Billing":
        assert res["review_recommended"] is True


def test_edge_case_genuine_billing(predictor):
    req = {
        "request_id": "TEST_BILLING",
        "request_text": "double charge on credit card for order KO2601948, please process refund",
        "channel": "email",
        "product_family": "Induction Cooktop",
        "warranty_status": "out_of_warranty",
    }
    res = predictor.predict_one(req)
    assert res["predicted_team"] == "Billing"
    assert res["confidence"] > 0.70


def test_edge_case_ambiguous_purifier(predictor):
    req = {
        "request_id": "TEST_AMBIGUOUS",
        "request_text": "please call me about my purifier",
        "channel": "chat",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
    }
    res = predictor.predict_one(req)
    assert res["predicted_team"] in CANONICAL_TEAMS
    assert res["review_recommended"] is True
