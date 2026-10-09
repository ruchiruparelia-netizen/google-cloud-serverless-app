"""Multi-channel telemetry tools for IVR, Mobile App, and Travel Registry."""

from typing import Dict, Any, List
import structlog
from ..config import DEFAULT_CUSTOMER
from ..models import ToolErrorRecoveryResponse
from ..observability import get_structured_logger

logger = get_structured_logger("jpmc_agent.tools.channel")


def query_telephony_ivr_logs(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Retrieves contact center IVR telephony session details and dropped call logs.

    Includes guided error handling returning structured LLM recovery instructions if the
    customer_id is invalid or telephony CDR storage is unavailable.

    Args:
        customer_id: The customer identifier.

    Returns:
        Recent IVR sessions, DTMF inputs, speech recognition logs, and premature disconnection records,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string.")

        logger.info(
            "telephony_ivr_logs_queried",
            tool_name="query_telephony_ivr_logs",
            customer_id=customer_id,
            session_id="ivr-sess-99412",
            outcome="AUTH_FAILED_INCOMPLETE",
        )
        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "recent_calls": [
                {
                    "session_id": "ivr-sess-99412",
                    "timestamp": "2026-09-07T14:32:00Z",
                    "duration_sec": 78,
                    "inbound_number": "+1 (555) 234-8901",
                    "intent_detected": "DISPUTE_DECLINE_CARD",
                    "last_prompt": "Please enter the 6-digit security passcode sent via text message to verify your identity.",
                    "disconnection_reason": "CALLER_DISCONNECTED_PREMATURELY",
                    "target_decline_amount": 142.50,
                    "outcome": "AUTH_FAILED_INCOMPLETE",
                }
            ],
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="query_telephony_ivr_logs",
            error_type="InvalidCustomerId",
            error=str(exc),
            fallback_tool="query_mobile_wallet_events",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_telephony_ivr_logs",
            error_type="InvalidCustomerId",
            error_message=str(exc),
            retryable=True,
            fallback_tool="query_mobile_wallet_events",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Pass a valid non-empty `customer_id` (default 'alex_morgan') and retry "
                "`query_telephony_ivr_logs(customer_id='alex_morgan')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="query_telephony_ivr_logs",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_telephony_ivr_logs",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Telephony CDR service is temporarily unavailable. Rely on preloaded "
                "Memory Bank context and `fetch_live_account_statement` to confirm the $142.50 Target decline."
            ),
        ).model_dump()


def query_mobile_wallet_events(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Queries mobile app sessions, device bindings, and digital wallet tokenization errors.

    Includes guided error handling with structured LLM recovery instructions on failure.

    Args:
        customer_id: The customer identifier.

    Returns:
        Digital wallet token requests, Apple Pay/Google Wallet push events, and error codes,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string.")

        logger.info(
            "mobile_wallet_events_queried",
            tool_name="query_mobile_wallet_events",
            customer_id=customer_id,
            error_code="CARD_STATUS_LOCKED_RESTRICTED",
        )
        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "device_model": "iPhone 16 Pro (iOS 18.2)",
            "app_version": "Chase Mobile v14.8.2",
            "recent_wallet_events": [
                {
                    "event_id": "ev-wallet-8812",
                    "timestamp": "2026-09-08T11:20:00Z",
                    "action": "PUSH_PROVISION_APPLE_WALLET",
                    "card_last4": "4821",
                    "result": "REJECTED_BY_ISSUER_NETWORK",
                    "error_code": "CARD_STATUS_LOCKED_RESTRICTED",
                    "gateway_response": "Token issuance blocked due to active security hold on primary account.",
                }
            ],
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="query_mobile_wallet_events",
            error_type="InvalidCustomerId",
            error=str(exc),
            fallback_tool="get_card_status",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_mobile_wallet_events",
            error_type="InvalidCustomerId",
            error_message=str(exc),
            retryable=True,
            fallback_tool="get_card_status",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Provide a valid `customer_id='alex_morgan'` and retry "
                "`query_mobile_wallet_events(customer_id='alex_morgan')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="query_mobile_wallet_events",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="get_card_status",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_mobile_wallet_events",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="get_card_status",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Mobile wallet telemetry service encountered an error. Fall back to "
                "`get_card_status(card_last4='4821')` to inspect `digital_wallet_tokens` directly."
            ),
        ).model_dump()


def query_travel_registry(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Queries verified travel itineraries and international trip notices on file.

    Includes guided error handling with actionable LLM recovery instructions if the
    customer_id is invalid or the travel registry is unreachable.

    Args:
        customer_id: The customer identifier.

    Returns:
        Active and upcoming travel destinations, verified hotel/lodging addresses, and travel dates,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string.")

        logger.info(
            "travel_registry_queried",
            tool_name="query_travel_registry",
            customer_id=customer_id,
            notice_id="TRV-88291-UK",
            destination="London, United Kingdom",
        )
        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "has_active_travel_notice": True,
            "active_notices": [
                {
                    "notice_id": "TRV-88291-UK",
                    "destination_country": "United Kingdom",
                    "destination_city": "London",
                    "start_date": "2026-09-28",
                    "end_date": "2026-10-12",
                    "verified_lodging_address": DEFAULT_CUSTOMER["current_travel_location"],
                    "emergency_courier_eligible": True,
                    "notes": "Customer traveling for international financial technology conference.",
                }
            ],
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="query_travel_registry",
            error_type="InvalidCustomerId",
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_travel_registry",
            error_type="InvalidCustomerId",
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Provide `customer_id='alex_morgan'` and retry "
                "`query_travel_registry(customer_id='alex_morgan')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="query_travel_registry",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_travel_registry",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Travel registry lookup failed. Fall back to `fetch_live_account_statement` "
                "to verify international POS activity in London, UK."
            ),
        ).model_dump()

