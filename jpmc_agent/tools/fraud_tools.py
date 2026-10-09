"""Fraud monitoring, velocity inspection, and dispute tools for JPMC Agent."""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog
from ..config import HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD
from ..models import ToolErrorRecoveryResponse, HumanInTheLoopInterrupt
from ..observability import get_structured_logger

logger = get_structured_logger("jpmc_agent.tools.fraud")


def query_fraud_velocity_alerts(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Inspects fraud velocity containment engine for geo-velocity alerts and anomalies.

    Includes guided error handling with structured LLM recovery instructions if the
    RiskOps velocity engine encounters an invalid customer_id or service timeout.

    Args:
        customer_id: The customer identifier.

    Returns:
        Risk score, geo-velocity alerts, concurrent session detections, and containment lock status,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string.")

        logger.info(
            "fraud_velocity_alerts_queried",
            tool_name="query_fraud_velocity_alerts",
            customer_id=customer_id,
            overall_risk_score=92,
            risk_level="CRITICAL",
        )
        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "overall_risk_score": 92,
            "risk_level": "CRITICAL",
            "containment_status": "SECURITY_LOCKED",
            "alerts": [
                {
                    "alert_id": "ALT-VEL-9921",
                    "type": "DUAL_CITY_GEO_VELOCITY",
                    "detected_at": "2026-09-07T09:15:00Z",
                    "location_a": {"city": "New York, NY", "ip": "198.51.100.4", "device": "MacBook Pro"},
                    "location_b": {"city": "Chicago, IL", "ip": "203.0.113.19", "device": "Windows POS/Browser"},
                    "delta_minutes": 9,
                    "physical_distance_miles": 712,
                    "action_taken": "IMMEDIATE_SECURITY_LOCK_PLACED",
                },
                {
                    "alert_id": "ALT-HIGH-VAL-1000",
                    "type": "HIGH_VALUE_UNFAMILIAR_MERCHANT",
                    "detected_at": "2026-09-07T09:14:00Z",
                    "merchant": "Chicago Luxury Electronics",
                    "amount": 1000.00,
                    "action_taken": "STEP_UP_CHALLENGE_FLAGGED",
                },
            ],
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="query_fraud_velocity_alerts",
            error_type="InvalidCustomerIdentifier",
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_fraud_velocity_alerts",
            error_type="InvalidCustomerIdentifier",
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Supply a valid non-empty customer_id (default: 'alex_morgan') and "
                "retry `query_fraud_velocity_alerts(customer_id='alex_morgan')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="query_fraud_velocity_alerts",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_fraud_velocity_alerts",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: RiskOps velocity telemetry is temporarily unreachable. Fall back to "
                "`fetch_live_account_statement(customer_id='alex_morgan')` to inspect flagged transactions directly."
            ),
        ).model_dump()


def audit_step_up_consent_logs(transaction_id: str = "tx-chi-1000") -> Dict[str, Any]:
    """Audits two-factor authentication and SMS Y/N step-up verification logs.

    Includes guided error handling with actionable LLM recovery instructions if the
    transaction_id is missing or malformed.

    Args:
        transaction_id: The ID of the transaction to audit (default 'tx-chi-1000').

    Returns:
        Step-up challenge history, outbound SMS timestamp, and reply verification status,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not transaction_id or not isinstance(transaction_id, str) or not transaction_id.strip():
            raise ValueError("transaction_id must be a non-empty string (e.g., 'tx-chi-1000').")

        logger.info(
            "step_up_consent_logs_audited",
            tool_name="audit_step_up_consent_logs",
            transaction_id=transaction_id,
            compromise_likelihood="HIGH",
        )
        return {
            "status": "SUCCESS",
            "transaction_id": transaction_id,
            "challenge_type": "SMS_STEP_UP_CONSENT",
            "outbound_phone": "+1 (555) 234-8901",
            "outbound_timestamp": "2026-09-07T09:14:15Z",
            "inbound_reply": "Y",
            "inbound_timestamp": "2026-09-07T09:14:38Z",
            "audit_note": (
                "SMS 'Y' reply received from secondary device IP 203.0.113.19 in Chicago while primary customer "
                "was established in New York/London. Highly suspicious credential relay or SIM-swap scenario. "
                "Containment lock justified."
            ),
            "compromise_likelihood": "HIGH",
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="audit_step_up_consent_logs",
            error_type="InvalidTransactionId",
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="audit_step_up_consent_logs",
            error_type="InvalidTransactionId",
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Call `fetch_live_account_statement()` first to obtain valid transaction IDs "
                "(such as 'tx-chi-1000'), then retry `audit_step_up_consent_logs(transaction_id='tx-chi-1000')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="audit_step_up_consent_logs",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="query_fraud_velocity_alerts",
        )
        return ToolErrorRecoveryResponse(
            tool_name="audit_step_up_consent_logs",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="query_fraud_velocity_alerts",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Step-up SMS log service encountered an unexpected error. Use "
                "`query_fraud_velocity_alerts(customer_id='alex_morgan')` to verify geo-velocity anomaly evidence."
            ),
        ).model_dump()


def file_fraud_dispute(
    transaction_id: str,
    amount: float,
    merchant: str,
    dispute_reason: str = "UNAUTHORIZED_FRAUDULENT_CHARGE",
    human_approved: bool = True,
    hitl_confirmation_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Auto-files a fraud dispute and issues immediate provisional credit under Reg E / Reg Z.

    Enforces a programmatic Human-in-the-Loop (HITL) code stop for high-stakes disputes
    exceeding HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD ($2,500.00) or when human_approved is False.
    Also includes guided error handling returning structured LLM recovery instructions on invalid inputs.

    Args:
        transaction_id: The ID of the unauthorized transaction (e.g., 'tx-chi-1000').
        amount: Transaction amount to credit (must be > 0).
        merchant: Merchant name.
        dispute_reason: Reason for dispute.
        human_approved: Whether customer/human confirmation has been granted for this action.
        hitl_confirmation_token: Optional supervisor/human approval token for high-value disputes.

    Returns:
        Dispute confirmation number, provisional credit amount, and ledger tracking status,
        or a HumanInTheLoopInterrupt / ToolErrorRecoveryResponse dictionary.
    """
    try:
        if not transaction_id or not str(transaction_id).strip():
            raise ValueError("transaction_id cannot be empty.")
        if amount is None or float(amount) <= 0:
            raise ValueError(f"Invalid dispute amount '{amount}'. Amount must be a positive number > 0.")
        if not merchant or not str(merchant).strip():
            raise ValueError("merchant name cannot be empty.")

        numeric_amount = float(amount)

        # PROGRAMMATIC HUMAN-IN-THE-LOOP (HITL) CODE STOP FOR HIGH-STAKES DISPUTES
        if not human_approved or (
            numeric_amount > HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD and not hitl_confirmation_token
        ):
            logger.info(
                "hitl_code_stop_triggered",
                tool_name="file_fraud_dispute",
                amount=numeric_amount,
                human_approved=human_approved,
            )
            return HumanInTheLoopInterrupt(
                interrupt_id=f"hitl-disp-{uuid.uuid4().hex[:8]}",
                action_name="file_fraud_dispute",
                risk_level="HIGH_VALUE_PROVISIONAL_CREDIT",
                reason=(
                    f"Dispute amount ${numeric_amount:,.2f} exceeds autonomous provisional credit threshold "
                    f"(${HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD:,.2f}) or lacks explicit human confirmation."
                ),
                proposed_arguments={
                    "transaction_id": transaction_id,
                    "amount": numeric_amount,
                    "merchant": merchant,
                    "dispute_reason": dispute_reason,
                },
                approval_instructions=(
                    "Ask the customer or Fraud Ops supervisor to explicitly confirm the high-value dispute "
                    "and re-invoke `file_fraud_dispute` with `human_approved=True` and a valid `hitl_confirmation_token`."
                ),
            ).model_dump()

        case_id = f"DSP-{uuid.uuid4().hex[:8].upper()}"
        logger.info(
            "fraud_dispute_filed",
            tool_name="file_fraud_dispute",
            dispute_case_id=case_id,
            transaction_id=transaction_id,
            amount=numeric_amount,
            merchant=merchant,
        )
        return {
            "status": "PROVISIONAL_CREDIT_POSTED",
            "dispute_case_id": case_id,
            "transaction_id": transaction_id,
            "merchant": merchant,
            "amount": numeric_amount,
            "provisional_credit_applied": True,
            "provisional_credit_amount": numeric_amount,
            "zero_liability_guarantee_applied": True,
            "estimated_resolution_days": 10,
            "filed_at": datetime.now(timezone.utc).isoformat(),
            "summary": (
                f"Dispute {case_id} successfully filed for ${numeric_amount:.2f} at {merchant}. "
                f"Under the JPMC Zero Liability policy, a provisional credit of ${numeric_amount:.2f} has been immediately applied."
            ),
        }
    except (ValueError, TypeError) as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="file_fraud_dispute",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="file_fraud_dispute",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Ensure `transaction_id` (e.g. 'tx-chi-1000'), a positive `amount` "
                "(e.g. 1000.00), and a non-empty `merchant` ('Chicago Luxury Electronics') are provided. "
                "Call `fetch_live_account_statement()` if you need to look up exact transaction details before retrying."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="file_fraud_dispute",
            error_type="DisputeGatewayError",
            error=str(exc),
            fallback_tool="execute_one_click_card_unlock_and_replacement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="file_fraud_dispute",
            error_type="DisputeGatewayError",
            error_message=str(exc),
            retryable=True,
            fallback_tool="execute_one_click_card_unlock_and_replacement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Standalone dispute filing encountered an error. You may retry "
                "`file_fraud_dispute` or invoke `execute_one_click_card_unlock_and_replacement` to execute "
                "atomic dispute filing alongside card replacement."
            ),
        ).model_dump()

