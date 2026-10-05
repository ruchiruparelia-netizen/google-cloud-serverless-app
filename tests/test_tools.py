"""Unit tests for JPMC Agent specialized tools."""

import pytest
from jpmc_agent.tools import (
    fetch_live_account_statement,
    get_card_status,
    query_fraud_velocity_alerts,
    audit_step_up_consent_logs,
    file_fraud_dispute,
    query_telephony_ivr_logs,
    query_mobile_wallet_events,
    query_travel_registry,
    validate_and_record_customer_claim,
    execute_one_click_card_unlock_and_replacement,
    provision_instant_virtual_card,
    dispatch_emergency_courier,
    query_knowledge_catalog,
)


def test_fetch_live_account_statement():
    data = fetch_live_account_statement("alex_morgan")
    assert data["customer_id"] == "alex_morgan"
    assert "4821" in data["account_number"]
    assert len(data["recent_transactions"]) >= 3
    # Check that $1,000 Chicago charge is present
    tx_1000 = next(t for t in data["recent_transactions"] if t["tx_id"] == "tx-chi-1000")
    assert tx_1000["amount"] == 1000.00
    assert tx_1000["flagged_fraud"] is True


def test_get_card_status():
    status = get_card_status("4821")
    assert status["status"] == "SECURITY_LOCKED"
    assert status["instant_vcn_eligible"] is True
    assert len(status["digital_wallet_tokens"]) > 0


def test_query_fraud_velocity_alerts():
    alerts = query_fraud_velocity_alerts("alex_morgan")
    assert alerts["overall_risk_score"] == 92
    assert alerts["containment_status"] == "SECURITY_LOCKED"
    assert len(alerts["alerts"]) >= 2
    geo_alert = next(a for a in alerts["alerts"] if a["type"] == "DUAL_CITY_GEO_VELOCITY")
    assert geo_alert["delta_minutes"] == 9
    assert geo_alert["physical_distance_miles"] == 712


def test_audit_step_up_consent_logs():
    audit = audit_step_up_consent_logs("tx-chi-1000")
    assert audit["transaction_id"] == "tx-chi-1000"
    assert audit["inbound_reply"] == "Y"
    assert audit["compromise_likelihood"] == "HIGH"


def test_file_fraud_dispute():
    res = file_fraud_dispute("tx-chi-1000", 1000.00, "Chicago Luxury Electronics")
    assert res["dispute_case_id"].startswith("DSP-")
    assert res["provisional_credit_applied"] is True
    assert res["provisional_credit_amount"] == 1000.00
    assert res["zero_liability_guarantee_applied"] is True


def test_channel_telemetry():
    ivr = query_telephony_ivr_logs("alex_morgan")
    assert len(ivr["recent_calls"]) == 1
    assert ivr["recent_calls"][0]["disconnection_reason"] == "CALLER_DISCONNECTED_PREMATURELY"

    mobile = query_mobile_wallet_events("alex_morgan")
    assert mobile["recent_wallet_events"][0]["error_code"] == "CARD_STATUS_LOCKED_RESTRICTED"

    travel = query_travel_registry("alex_morgan")
    assert travel["has_active_travel_notice"] is True
    assert "The Savoy Hotel" in travel["active_notices"][0]["verified_lodging_address"]


def test_5_avenue_claim_veracity_validator():
    # London stolen wallet claim
    eval_london = validate_and_record_customer_claim("alex_morgan", "Someone stole my wallet in London!")
    assert eval_london["veracity_status"] == "VERIFIED_TRUE"
    assert eval_london["confidence_score"] >= 0.95
    assert len(eval_london["relevant_avenues_checked"]) == 5
    assert any("The Savoy Hotel" in c for c in eval_london["corroborating_telemetry"])

    # Chicago fraud claim
    eval_chi = validate_and_record_customer_claim("alex_morgan", "I did not make the $1,000 charge in Chicago.")
    assert eval_chi["veracity_status"] == "VERIFIED_TRUE"
    assert eval_chi["confidence_score"] >= 0.95
    assert any("RiskOps Velocity" in c for c in eval_chi["corroborating_telemetry"])


def test_provision_instant_virtual_card():
    vcn = provision_instant_virtual_card("alex_morgan")
    assert vcn["status"] == "ACTIVE_PROVISIONED"
    assert vcn["push_to_apple_wallet_ready"] is True
    assert vcn["push_to_google_wallet_ready"] is True
    assert len(vcn["cvv"]) == 3
    assert len(vcn["last4"]) == 4


def test_dispatch_emergency_courier():
    courier = dispatch_emergency_courier("alex_morgan")
    assert courier["status"] == "DISPATCHED_TO_COURIER"
    assert "FedEx" in courier["carrier"]
    assert "The Savoy Hotel" in courier["destination_address"]


def test_execute_one_click_card_unlock_and_replacement():
    res = execute_one_click_card_unlock_and_replacement("alex_morgan")
    assert res["resolution_status"] == "SUCCESS"
    assert res["old_card_action"] == "PERMANENTLY_REVOKED_AND_BLOCKED"
    assert len(res["disputed_transactions"]) == 1
    assert res["virtual_card"]["status"] == "ACTIVE_PROVISIONED"
    assert res["emergency_courier"]["status"] == "DISPATCHED_TO_COURIER"
    assert len(res["updated_billers_notified"]) >= 4
