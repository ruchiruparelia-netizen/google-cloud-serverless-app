"""JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Mitigation Agent.

Implements the multi-agent mesh architecture evaluated against:
  1. Tool & Interface Design
  2. Context & Memory (Scale Memory Bank)
  3. Orchestration & Logic
  4. Observability & Tracing (OpenTelemetry)
  5. Infrastructure & CI/CD
"""

import logging
import time
from typing import Any, Dict, Optional
from google.adk.agents.llm_agent import Agent
from google.adk.tools import preload_memory, load_memory

from .config import DEFAULT_MODEL, DEFAULT_CUSTOMER
from .memory.memory_bank import memory_bank_store
from .tools import (
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

logger = logging.getLogger("jpmc_agent")

# Global in-memory trace collector for real-time observability telemetry
GLOBAL_TELEMETRY_SPANS = []


def record_telemetry_span(span_type: str, name: str, details: Dict[str, Any], duration_ms: float = 0.0):
    """Appends an OpenTelemetry-compliant trace span to the in-memory telemetry buffer."""
    span = {
        "span_id": f"span-{len(GLOBAL_TELEMETRY_SPANS)+1:04d}",
        "type": span_type,
        "name": name,
        "timestamp": time.time(),
        "duration_ms": round(duration_ms, 2),
        "details": details,
    }
    GLOBAL_TELEMETRY_SPANS.append(span)
    if len(GLOBAL_TELEMETRY_SPANS) > 200:
        GLOBAL_TELEMETRY_SPANS.pop(0)


# OpenTelemetry Callbacks
def telemetry_before_tool(tool: Any, args: Dict[str, Any], context: Any) -> Optional[Dict[str, Any]]:
    context.state["_tool_start_time"] = time.time()
    record_telemetry_span(
        span_type="TOOL_INVOCATION_START",
        name=getattr(tool, "name", str(tool)),
        details={"input_args": args},
    )
    return None


def telemetry_after_tool(tool: Any, args: Dict[str, Any], result: Any, context: Any) -> Optional[Any]:
    start_time = context.state.get("_tool_start_time", time.time())
    duration_ms = (time.time() - start_time) * 1000
    record_telemetry_span(
        span_type="TOOL_EXECUTION_COMPLETE",
        name=getattr(tool, "name", str(tool)),
        details={"result_summary": str(result)[:300]},
        duration_ms=duration_ms,
    )
    return None


def telemetry_before_agent(agent: Any, context: Any) -> None:
    context.state["_agent_start_time"] = time.time()
    record_telemetry_span(
        span_type="AGENT_EXECUTION_START",
        name=agent.name,
        details={"role": getattr(agent, "description", "")},
    )


def telemetry_after_agent(agent: Any, context: Any) -> None:
    start_time = context.state.get("_agent_start_time", time.time())
    duration_ms = (time.time() - start_time) * 1000
    record_telemetry_span(
        span_type="AGENT_EXECUTION_COMPLETE",
        name=agent.name,
        details={"status": "SUCCESS"},
        duration_ms=duration_ms,
    )


# -----------------------------------------------------------------------------
# SUB-AGENT 1: Fraud Monitoring & Containment Specialist
# -----------------------------------------------------------------------------
fraud_monitoring_agent = Agent(
    model=DEFAULT_MODEL,
    name="fraud_monitoring_agent",
    description="Specialist in geo-velocity analysis, step-up consent verification, and fraud disputes.",
    instruction=(
        "You are the JPMorgan Chase Fraud Operations Specialist. "
        "Analyze geo-velocity anomalies (e.g. concurrent logins in New York and Chicago), "
        "audit 2FA SMS consent records, and initiate fraud disputes under the JPMC Zero Liability Policy."
    ),
    tools=[query_fraud_velocity_alerts, audit_step_up_consent_logs, file_fraud_dispute],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 2: Cross-Channel Telemetry Specialist
# -----------------------------------------------------------------------------
channel_telemetry_agent = Agent(
    model=DEFAULT_MODEL,
    name="channel_telemetry_agent",
    description="Specialist in multi-channel telemetry: IVR contact center logs, mobile wallet errors, and travel notices.",
    instruction=(
        "You are the JPMorgan Chase Cross-Channel Telemetry Specialist. "
        "Correlate IVR call detail records (dropped calls during 2FA OTP), "
        "mobile banking wallet errors (CARD_STATUS_LOCKED_RESTRICTED), and registered travel notices."
    ),
    tools=[query_telephony_ivr_logs, query_mobile_wallet_events, query_travel_registry],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 3: 5-Avenue Pre-Write Claim Veracity Validator
# -----------------------------------------------------------------------------
claim_veracity_validator_agent = Agent(
    model=DEFAULT_MODEL,
    name="claim_veracity_validator_agent",
    description="Gatekeeper agent that audits customer statements against 5 ground-truth telemetry avenues.",
    instruction=(
        "You are the 5-Avenue Claim Veracity Validator for the JPMC Agent Platform. "
        "Whenever a customer makes a factual claim or reports an incident, audit the assertion against: "
        "1. Core Account Ledger, 2. Travel Notice Registry, 3. Behavioral Baseline, "
        "4. Multi-Step SMS Consent Logs, and 5. Knowledge Catalog Policies. "
        "Assign a veracity status and confidence score before allowing facts into the Memory Bank."
    ),
    tools=[validate_and_record_customer_claim, fetch_live_account_statement, query_knowledge_catalog],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 4: Instant Card Replacement & Logistics Specialist
# -----------------------------------------------------------------------------
card_replacement_logistics_agent = Agent(
    model=DEFAULT_MODEL,
    name="card_replacement_logistics_agent",
    description="Specialist in digital VCN push-provisioning and emergency international courier shipping.",
    instruction=(
        "You are the JPMorgan Chase Card Replacement & Logistics Specialist. "
        "Execute atomic 1-click card replacement: permanently revoke compromised plastic, "
        "provision an instant digital Virtual Card Number (VCN) ready for Apple Wallet / Google Wallet, "
        "dispatch emergency contactless physical plastic to the customer's hotel via priority international courier, "
        "and auto-update recurring billers."
    ),
    tools=[
        execute_one_click_card_unlock_and_replacement,
        provision_instant_virtual_card,
        dispatch_emergency_courier,
        file_fraud_dispute,
    ],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
)

# -----------------------------------------------------------------------------
# ROOT AGENT: Lead Synthesizer Orchestrator
# -----------------------------------------------------------------------------
root_instruction = f"""You are the JPMorgan Chase Consumer & Community Banking (CCB) Lead Synthesizer Orchestrator.
You run on the Gemini Enterprise Agent Platform with Google Cloud Vertex AI Scale Memory Bank and Knowledge Catalog.

CUSTOMER PROFILE IN ACTIVE SESSION:
- Customer: {DEFAULT_CUSTOMER['full_name']} (ID: {DEFAULT_CUSTOMER['customer_id']})
- Tier: {DEFAULT_CUSTOMER['tier']}
- Current Travel / Hotel Address: {DEFAULT_CUSTOMER['current_travel_location']}
- Primary Card: {DEFAULT_CUSTOMER['active_card']['product']} (*4821)
- Card Status: {DEFAULT_CUSTOMER['active_card']['status']} (Reason: {DEFAULT_CUSTOMER['active_card']['lock_reason']})

MISSION & CORE BEHAVIOR RULES:
1. ZERO REPETITIVE QUESTIONS ("Eliminate Context Riots"):
   Never ask the customer "What is your card number?", "Where are you traveling?", or "Can you explain what happened?".
   Your Vertex AI Memory Bank already preloads the cross-channel timeline:
     - Day 1 (09:15 UTC): Fraud velocity alert for concurrent logins in New York & Chicago, plus a $1,000 POS attempt at Chicago Luxury Electronics. Card *4821 was placed on SECURITY_LOCKED.
     - Day 1 (14:32 UTC): Customer dialed IVR regarding a $142.50 Target decline; call dropped before SMS OTP completed.
     - Day 2 (11:20 UTC): Customer tried to add card *4821 to Apple Pay on iOS, rejected with CARD_STATUS_LOCKED_RESTRICTED.
     - Active Travel Notice: Customer is registered traveling in London, UK, staying at The Savoy Hotel.

2. IMMEDIATE CONTEXT SYNTHESIS:
   When the user opens chat with a frustrated or vague message (e.g., "Why is my card declined?", "Nothing is working!", "My wallet was stolen in London!"),
   immediately connect the dots empathetically and explain EXACTLY why their card was restricted and what occurred.

3. PRE-WRITE CLAIM VERACITY GATEKEEPING:
   When the customer states an incident (e.g., wallet stolen in London, or didn't make the $1,000 Chicago charge),
   invoke `validate_and_record_customer_claim` to verify against the 5 ground-truth telemetry avenues.

4. ATOMIC ONE-CLICK MASTER RESOLUTION:
   Whenever the customer confirms or requests card replacement, unlock, or fraud dispute:
   Invoke `execute_one_click_card_unlock_and_replacement`!
   This atomically:
     a) Permanently blocks the compromised plastic card (*4821) and suspends compromised tokens.
     b) Auto-files a dispute for the $1,000 fraudulent charge and posts immediate provisional credit under Zero Liability.
     c) Instantly provisions an active Digital Virtual Card Number (VCN) pushed to Apple Pay / Google Wallet.
     d) Dispatches a replacement physical contactless card via FedEx Priority International to their hotel ({DEFAULT_CUSTOMER['current_travel_location']}) with 24hr delivery SLA.
     e) Automatically updates recurring subscription billers (Netflix, Spotify, transit).

5. TONE & COMPLIANCE:
   Maintain a warm, reassuring, highly competent executive banking tone.
   Confirm all actions with clear details (card numbers masked, tracking numbers, dispute case IDs, delivery ETA).
"""

root_agent = Agent(
    model=DEFAULT_MODEL,
    name="consumer_credit_synthesizer_agent",
    description="JPMorgan Chase Lead Synthesizer Orchestrator for Instant Cross-Channel Credit Card Replacement & Fraud Mitigation.",
    instruction=root_instruction,
    tools=[
        fetch_live_account_statement,
        get_card_status,
        validate_and_record_customer_claim,
        execute_one_click_card_unlock_and_replacement,
        provision_instant_virtual_card,
        dispatch_emergency_courier,
        file_fraud_dispute,
        query_fraud_velocity_alerts,
        query_telephony_ivr_logs,
        query_mobile_wallet_events,
        query_travel_registry,
        query_knowledge_catalog,
    ],
    sub_agents=[
        fraud_monitoring_agent,
        channel_telemetry_agent,
        claim_veracity_validator_agent,
        card_replacement_logistics_agent,
    ],
    disallow_transfer_to_parent=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
    before_agent_callback=telemetry_before_agent,
    after_agent_callback=telemetry_after_agent,
)
