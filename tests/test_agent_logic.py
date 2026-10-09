"""Integration tests for JPMC Agent mesh and FastAPI web server endpoints."""

import pytest
from fastapi.testclient import TestClient
from web_server import app
from jpmc_agent.agent import root_agent, fraud_monitoring_agent, card_replacement_logistics_agent

client = TestClient(app)


def test_agent_mesh_structure():
    assert root_agent.name == "consumer_credit_synthesizer_agent"
    assert len(root_agent.tools) >= 10
    assert len(root_agent.sub_agents) == 4
    sub_agent_names = {sa.name for sa in root_agent.sub_agents}
    assert "fraud_monitoring_agent" in sub_agent_names
    assert "channel_telemetry_agent" in sub_agent_names
    assert "claim_veracity_validator_agent" in sub_agent_names
    assert "card_replacement_logistics_agent" in sub_agent_names


def test_health_check_endpoint():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["agent_name"] == "consumer_credit_synthesizer_agent"


def test_agents_list_endpoint():
    resp = client.get("/api/agents/list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    names = [a["name"] for a in data["agents"]]
    assert "consumer_credit_synthesizer_agent" in names
    assert "card_replacement_logistics_agent" in names


def test_rubric_scores_endpoint():
    resp = client.get("/api/rubric/scores")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_score"] == 95
    assert data["max_score"] == 95
    assert data["percentage"] == "100.0%"
    assert len(data["pillars"]) == 5


def test_chat_endpoint_why_declined():
    resp = client.post("/api/chat", json={"message": "Why was my card declined at Target?", "customer_id": "alex_morgan"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Target Store #1142" in data["reply"]
    assert "SECURITY_LOCKED" in data["reply"]
    assert "Chicago" in data["reply"]
    assert data["latency_ms"] >= 0


def test_chat_endpoint_one_click_resolution():
    resp = client.post("/api/chat", json={"message": "Yes, execute the 1-click replacement, dispute, and emergency courier!", "customer_id": "alex_morgan"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_executed"] == "ONE_CLICK_RESOLUTION"
    res = data["action_data"]
    assert res["virtual_card"]["status"] == "ACTIVE_PROVISIONED"
    assert res["emergency_courier"]["status"] == "DISPATCHED_TO_COURIER"
    assert "FedEx" in res["emergency_courier"]["carrier"]
    assert "The Savoy Hotel" in res["emergency_courier"]["destination_address"]


def test_telemetry_spans_endpoint():
    resp = client.get("/api/telemetry/spans")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    span_types = {s["type"] for s in data["spans"]}
    assert "PRELOAD_MEMORY_RECALL" in span_types


def test_token_usage_summary_endpoint():
    resp = client.get("/api/telemetry/tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cumulative_input_tokens"] > 0
    assert data["cumulative_output_tokens"] > 0
    assert data["total_tokens"] == data["cumulative_input_tokens"] + data["cumulative_output_tokens"]
    assert "last_turn" in data
    assert data["last_turn"]["input_tokens"] > 0
    assert data["last_turn"]["output_tokens"] > 0

