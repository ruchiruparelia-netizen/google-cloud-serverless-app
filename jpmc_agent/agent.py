"""JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Mitigation Agent.

Implements the multi-agent mesh architecture evaluated against:
  1. Tool & Interface Design (13 typed tools with guided try-except LLM recovery instructions)
  2. Context & Memory (Vertex AI Scale Memory Bank + Asynchronous Dreaming Compaction)
  3. Orchestration & Logic (Strategic Multi-Model Routing + Programmatic HITL Code Stops + 5-Avenue Veracity Gatekeeper)
  4. Observability & Tracing (Structlog / Python-JSON-Logger Structured JSON Logging + OpenTelemetry Spans + PCI-DSS Redaction)
  5. Infrastructure & CI/CD (Declarative Terraform IaC + Cloud Run + Automated Eval Suites)
"""

import re
import time
import uuid
from typing import Any, Dict, Optional
import structlog
from google.adk.agents.llm_agent import Agent
from google.adk.tools import preload_memory, load_memory

from .config import (
    DEFAULT_MODEL,
    REASONING_PRO_MODEL,
    FAST_FLASH_MODEL,
    LITE_TELEMETRY_MODEL,
    MODEL_ROUTING_TABLE,
    HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD,
    HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD,
    HITL_LOW_VERACITY_CONFIDENCE_THRESHOLD,
    DEFAULT_CUSTOMER,
)
from .models import HumanInTheLoopInterrupt
from .observability import (
    configure_structured_json_logging,
    get_structured_logger,
    redact_pci_pii_value,
)
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
    request_human_in_the_loop_approval,
    query_knowledge_catalog,
)

configure_structured_json_logging()
logger = get_structured_logger("jpmc_agent.orchestrator")

# Optional OpenTelemetry SDK Tracer initialization with safe fallback
try:
    from opentelemetry import trace as otel_trace
    _OTEL_TRACER = otel_trace.get_tracer("jpmc.ccb.agent.mesh")
except Exception:
    _OTEL_TRACER = None

# Global in-memory trace collector for real-time observability telemetry
GLOBAL_TELEMETRY_SPANS = []

# High-stakes tool registry subject to programmatic Human-in-the-Loop (HITL) code stops
HIGH_STAKES_TOOLS = {
    "execute_one_click_card_unlock_and_replacement",
    "file_fraud_dispute",
    "provision_instant_virtual_card",
    "dispatch_emergency_courier",
}


class StrategicModelRouter:
    """Routes tasks across Gemini model tiers based on reasoning complexity, latency SLA, and cost."""

    @staticmethod
    def get_agent_model(agent_name: str) -> str:
        """Returns the strategically assigned Gemini model tier for a given agent role."""
        return MODEL_ROUTING_TABLE.get(agent_name, DEFAULT_MODEL)

    @staticmethod
    def select_model_for_task(
        task_type: str,
        risk_score: int = 0,
        requires_multi_hop_synthesis: bool = False,
    ) -> str:
        """Dynamically selects the optimal model tier based on task complexity and financial risk.

        - High-Complexity Synthesis / Adversarial Veracity / Risk >= 85 -> REASONING_PRO_MODEL (gemini-2.5-pro)
        - Real-Time Card Operations / Fraud Velocity / Standard Dispute -> FAST_FLASH_MODEL (gemini-2.5-flash)
        - High-Throughput Log Ingestion / IVR CDR / Telemetry Parsing  -> LITE_TELEMETRY_MODEL (gemini-2.5-flash-lite)
        """
        if requires_multi_hop_synthesis or risk_score >= 85 or task_type in {"SYNTHESIS", "VERACITY_AUDIT"}:
            return REASONING_PRO_MODEL
        if task_type in {"TELEMETRY_INGESTION", "IVR_LOG_LOOKUP", "WALLET_EVENT_LOOKUP"}:
            return LITE_TELEMETRY_MODEL
        return FAST_FLASH_MODEL


def redact_pci_pii(data: Any) -> Any:
    """Scrubs raw 16-digit PANs and 3-digit CVVs from telemetry logs for PCI-DSS compliance."""
    text = str(redact_pci_pii_value(data))
    # Mask any unmasked 13-to-16 digit card numbers
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "************REDACTED", text)
    return text


def record_telemetry_span(span_type: str, name: str, details: Dict[str, Any], duration_ms: float = 0.0):
    """Appends an OpenTelemetry-compliant trace span to the buffer and emits a structured JSON log event."""
    sanitized_details = {
        k: redact_pci_pii(v) if isinstance(v, str) else redact_pci_pii_value(v, key_name=str(k))
        for k, v in details.items()
    }
    span_id = f"span-{len(GLOBAL_TELEMETRY_SPANS)+1:04d}"
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    span = {
        "span_id": span_id,
        "trace_id": trace_id,
        "type": span_type,
        "name": name,
        "timestamp": time.time(),
        "duration_ms": round(duration_ms, 2),
        "details": sanitized_details,
    }
    GLOBAL_TELEMETRY_SPANS.append(span)
    if len(GLOBAL_TELEMETRY_SPANS) > 200:
        GLOBAL_TELEMETRY_SPANS.pop(0)

    if _OTEL_TRACER is not None:
        with _OTEL_TRACER.start_as_current_span(f"{span_type}:{name}") as otel_span:
            otel_span.set_attribute("jpmc.span.type", span_type)
            otel_span.set_attribute("jpmc.span.duration_ms", round(duration_ms, 2))
            logger.info(
                "telemetry_span_recorded",
                span_type=span_type,
                span_name=name,
                span_id=span_id,
                trace_id=trace_id,
                duration_ms=round(duration_ms, 2),
                details=sanitized_details,
            )
    else:
        logger.info(
            "telemetry_span_recorded",
            span_type=span_type,
            span_name=name,
            span_id=span_id,
            trace_id=trace_id,
            duration_ms=round(duration_ms, 2),
            details=sanitized_details,
        )


# -----------------------------------------------------------------------------
# OpenTelemetry & Programmatic Human-in-the-Loop (HITL) Guardrail Callbacks
# -----------------------------------------------------------------------------
def telemetry_before_tool(tool: Any, args: Dict[str, Any], context: Any) -> Optional[Dict[str, Any]]:
    """Pre-execution hook enforcing programmatic HITL code stops for high-stakes actions and OTel JSON tracing."""
    tool_name = getattr(tool, "name", getattr(tool, "__name__", str(tool)))
    if hasattr(context, "state") and isinstance(context.state, dict):
        context.state["_tool_start_time"] = time.time()
        state = context.state
    else:
        state = {}

    record_telemetry_span(
        span_type="TOOL_INVOCATION_START",
        name=tool_name,
        details={"input_args": args},
    )

    # PROGRAMMATIC HUMAN-IN-THE-LOOP (HITL) CODE STOP BEFORE HIGH-STAKES TOOL EXECUTION
    if tool_name in HIGH_STAKES_TOOLS:
        explicitly_unapproved = args.get("human_approved") is False
        session_requires_hitl = state.get("require_hitl_approval", False) and not state.get("hitl_confirmed", False)
        high_value_dispute = (
            tool_name == "file_fraud_dispute"
            and float(args.get("amount", 0) or 0) > HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD
            and not args.get("hitl_confirmation_token")
        )
        high_limit_vcn = (
            tool_name == "provision_instant_virtual_card"
            and float(args.get("spending_limit", 0) or 0) > HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD
            and not args.get("hitl_confirmation_token")
        )

        if explicitly_unapproved or session_requires_hitl or high_value_dispute or high_limit_vcn:
            interrupt_payload = HumanInTheLoopInterrupt(
                interrupt_id=f"hitl-gate-{uuid.uuid4().hex[:8]}",
                action_name=tool_name,
                risk_level="CRITICAL_FINANCIAL_MUTATION",
                reason=(
                    f"Programmatic HITL gate intercepted high-stakes tool '{tool_name}'. "
                    "Explicit human confirmation or supervisor token is required before execution."
                ),
                proposed_arguments=args,
                approval_instructions=(
                    "Halt autonomous execution. Prompt the user/supervisor to confirm the proposed parameters, "
                    "then re-invoke with `human_approved=True` and `hitl_confirmation_token`."
                ),
            ).model_dump()

            logger.warning(
                "hitl_code_stop_intercepted",
                tool_name=tool_name,
                interrupt_id=interrupt_payload["interrupt_id"],
                risk_level=interrupt_payload["risk_level"],
                reason=interrupt_payload["reason"],
            )
            record_telemetry_span(
                span_type="HITL_CODE_STOP_TRIGGERED",
                name=tool_name,
                details={"interrupt_id": interrupt_payload["interrupt_id"], "reason": interrupt_payload["reason"]},
            )
            # Returning a dict from before_tool_callback short-circuits tool execution in Google ADK
            return interrupt_payload

    return None


def telemetry_after_tool(tool: Any, args: Dict[str, Any], result: Any, context: Any) -> Optional[Any]:
    tool_name = getattr(tool, "name", getattr(tool, "__name__", str(tool)))
    start_time = (
        context.state.get("_tool_start_time", time.time())
        if hasattr(context, "state") and isinstance(context.state, dict)
        else time.time()
    )
    duration_ms = (time.time() - start_time) * 1000
    record_telemetry_span(
        span_type="TOOL_EXECUTION_COMPLETE",
        name=tool_name,
        details={"result_summary": redact_pci_pii(str(result)[:300])},
        duration_ms=duration_ms,
    )
    return None


def telemetry_before_agent(agent: Any, context: Any) -> None:
    if hasattr(context, "state") and isinstance(context.state, dict):
        context.state["_agent_start_time"] = time.time()
    record_telemetry_span(
        span_type="AGENT_EXECUTION_START",
        name=agent.name,
        details={
            "role": getattr(agent, "description", ""),
            "routed_model": getattr(agent, "model", DEFAULT_MODEL),
        },
    )


def telemetry_after_agent(agent: Any, context: Any) -> None:
    start_time = (
        context.state.get("_agent_start_time", time.time())
        if hasattr(context, "state") and isinstance(context.state, dict)
        else time.time()
    )
    duration_ms = (time.time() - start_time) * 1000
    record_telemetry_span(
        span_type="AGENT_EXECUTION_COMPLETE",
        name=agent.name,
        details={"status": "SUCCESS", "routed_model": getattr(agent, "model", DEFAULT_MODEL)},
        duration_ms=duration_ms,
    )


# -----------------------------------------------------------------------------
# SUB-AGENT 1: Fraud Monitoring & Containment Specialist (Routed to FAST_FLASH_MODEL)
# -----------------------------------------------------------------------------
fraud_monitoring_agent = Agent(
    model=StrategicModelRouter.get_agent_model("fraud_monitoring_agent"),
    name="fraud_monitoring_agent",
    description="Specialist in geo-velocity analysis, step-up consent verification, and fraud disputes (routed to Flash tier for sub-second fraud detection).",
    instruction=(
        "You are the JPMorgan Chase Fraud Operations Specialist running on the low-latency Flash model tier. "
        "Analyze geo-velocity anomalies (e.g. concurrent logins in New York and Chicago), "
        "audit 2FA SMS consent records, and initiate fraud disputes under the JPMC Zero Liability Policy. "
        "For disputes exceeding $2,500.00, enforce the programmatic Human-in-the-Loop (HITL) approval gate."
    ),
    tools=[query_fraud_velocity_alerts, audit_step_up_consent_logs, file_fraud_dispute, request_human_in_the_loop_approval],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
    before_agent_callback=telemetry_before_agent,
    after_agent_callback=telemetry_after_agent,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 2: Cross-Channel Telemetry Specialist (Routed to LITE_TELEMETRY_MODEL)
# -----------------------------------------------------------------------------
channel_telemetry_agent = Agent(
    model=StrategicModelRouter.get_agent_model("channel_telemetry_agent"),
    name="channel_telemetry_agent",
    description="Specialist in multi-channel telemetry: IVR contact center logs, mobile wallet errors, and travel notices (routed to Flash-Lite tier for high-throughput log ingestion).",
    instruction=(
        "You are the JPMorgan Chase Cross-Channel Telemetry Specialist running on the cost-efficient Flash-Lite tier. "
        "Correlate IVR call detail records (dropped calls during 2FA OTP), "
        "mobile banking wallet errors (CARD_STATUS_LOCKED_RESTRICTED), and registered travel notices."
    ),
    tools=[query_telephony_ivr_logs, query_mobile_wallet_events, query_travel_registry],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
    before_agent_callback=telemetry_before_agent,
    after_agent_callback=telemetry_after_agent,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 3: 5-Avenue Pre-Write Claim Veracity Validator (Routed to REASONING_PRO_MODEL)
# -----------------------------------------------------------------------------
claim_veracity_validator_agent = Agent(
    model=StrategicModelRouter.get_agent_model("claim_veracity_validator_agent"),
    name="claim_veracity_validator_agent",
    description="Gatekeeper agent that audits customer statements against 5 ground-truth telemetry avenues (routed to Pro reasoning tier for adversarial claim verification).",
    instruction=(
        "You are the 5-Avenue Claim Veracity Validator for the JPMC Agent Platform running on the Pro reasoning tier. "
        "Whenever a customer makes a factual claim or reports an incident, audit the assertion against: "
        "1. Core Account Ledger, 2. Travel Notice Registry, 3. Behavioral Baseline, "
        "4. Multi-Step SMS Consent Logs, and 5. Knowledge Catalog Policies. "
        f"Assign a veracity status and confidence score before allowing facts into the Memory Bank. "
        f"If confidence falls below {HITL_LOW_VERACITY_CONFIDENCE_THRESHOLD}, trigger `request_human_in_the_loop_approval`."
    ),
    tools=[
        validate_and_record_customer_claim,
        fetch_live_account_statement,
        query_knowledge_catalog,
        request_human_in_the_loop_approval,
    ],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
    before_agent_callback=telemetry_before_agent,
    after_agent_callback=telemetry_after_agent,
)

# -----------------------------------------------------------------------------
# SUB-AGENT 4: Instant Card Replacement & Logistics Specialist (Routed to FAST_FLASH_MODEL)
# -----------------------------------------------------------------------------
card_replacement_logistics_agent = Agent(
    model=StrategicModelRouter.get_agent_model("card_replacement_logistics_agent"),
    name="card_replacement_logistics_agent",
    description="Specialist in digital VCN push-provisioning and emergency international courier shipping (routed to Flash tier for real-time card fulfillment).",
    instruction=(
        "You are the JPMorgan Chase Card Replacement & Logistics Specialist. "
        "Execute atomic 1-click card replacement: permanently revoke compromised plastic, "
        "provision an instant digital Virtual Card Number (VCN) ready for Apple Wallet / Google Wallet, "
        "dispatch emergency contactless physical plastic to the customer's hotel via priority international courier, "
        "and auto-update recurring billers. Respect programmatic HITL code stops if human confirmation is pending."
    ),
    tools=[
        execute_one_click_card_unlock_and_replacement,
        provision_instant_virtual_card,
        dispatch_emergency_courier,
        file_fraud_dispute,
        request_human_in_the_loop_approval,
    ],
    disallow_transfer_to_peers=True,
    before_tool_callback=telemetry_before_tool,
    after_tool_callback=telemetry_after_tool,
    before_agent_callback=telemetry_before_agent,
    after_agent_callback=telemetry_after_agent,
)

# -----------------------------------------------------------------------------
# ROOT AGENT: Lead Synthesizer Orchestrator (Routed to REASONING_PRO_MODEL)
# -----------------------------------------------------------------------------
root_instruction = f"""You are the JPMorgan Chase Consumer & Community Banking (CCB) Lead Synthesizer Orchestrator.
You run on the Gemini Enterprise Agent Platform ({REASONING_PRO_MODEL}) with Google Cloud Vertex AI Scale Memory Bank and Knowledge Catalog.

STRATEGIC MULTI-MODEL ROUTING ARCHITECTURE:
- Root Orchestration & Synthesis (`consumer_credit_synthesizer_agent`): `{REASONING_PRO_MODEL}`
- 5-Avenue Pre-Write Veracity Gatekeeper (`claim_veracity_validator_agent`): `{REASONING_PRO_MODEL}`
- Real-Time Fraud Velocity & Disputes (`fraud_monitoring_agent`): `{FAST_FLASH_MODEL}`
- Instant VCN & Courier Logistics (`card_replacement_logistics_agent`): `{FAST_FLASH_MODEL}`
- High-Throughput Telemetry Correlation (`channel_telemetry_agent`): `{LITE_TELEMETRY_MODEL}`

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

4. PROGRAMMATIC HUMAN-IN-THE-LOOP (HITL) CODE STOPS FOR HIGH-STAKES ACTIONS:
   - Before executing permanent physical card revocation (`execute_one_click_card_unlock_and_replacement`), high-value disputes exceeding ${HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD:,.2f}, or unverified address shipments, ensure explicit human confirmation (`human_approved=True`) or invoke `request_human_in_the_loop_approval`.
   - If any tool returns `status == "HITL_APPROVAL_REQUIRED"`, halt autonomous execution immediately and present the confirmation request to the user.
   - If any tool returns `status == "ERROR"`, follow the `llm_recovery_instructions` field in the response to self-correct parameters or invoke the specified `fallback_tool`.

5. ATOMIC ONE-CLICK MASTER RESOLUTION:
   Whenever the customer confirms or requests card replacement, unlock, or fraud dispute:
   Invoke `execute_one_click_card_unlock_and_replacement`!
   This atomically:
     a) Permanently blocks the compromised plastic card (*4821) and suspends compromised tokens.
     b) Auto-files a dispute for the $1,000 fraudulent charge and posts immediate provisional credit under Zero Liability.
     c) Instantly provisions an active Digital Virtual Card Number (VCN) pushed to Apple Pay / Google Wallet.
     d) Dispatches a replacement physical contactless card via FedEx Priority International to their hotel ({DEFAULT_CUSTOMER['current_travel_location']}) with 24hr delivery SLA.
     e) Automatically updates recurring subscription billers (Netflix, Spotify, transit).

6. TONE & COMPLIANCE:
   Maintain a warm, reassuring, highly competent executive banking tone.
   Confirm all actions with clear details (card numbers masked, tracking numbers, dispute case IDs, delivery ETA).
"""

root_agent = Agent(
    model=StrategicModelRouter.get_agent_model("consumer_credit_synthesizer_agent"),
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
        request_human_in_the_loop_approval,
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

