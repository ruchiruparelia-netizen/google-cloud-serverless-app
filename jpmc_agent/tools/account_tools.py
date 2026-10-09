"""Account, core ledger, and card status tools for JPMC Agent."""

from typing import Dict, Any, List
import structlog
from ..config import DEFAULT_CUSTOMER
from ..models import ToolErrorRecoveryResponse
from ..observability import get_structured_logger

logger = get_structured_logger("jpmc_agent.tools.account")


def fetch_live_account_statement(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Retrieves real-time account ledger statement, pending authorizations, and current balances.

    Includes guided error handling that returns structured LLM recovery instructions if the
    customer identifier is invalid or the core ledger service encounters an error.

    Args:
        customer_id: The unique identifier of the customer (defaults to 'alex_morgan').

    Returns:
        A dictionary containing core banking ledger details, current balance, and recent transactions,
        or a structured ToolErrorRecoveryResponse with actionable LLM recovery instructions on failure.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string identifier.")

        normalized_id = customer_id.strip().lower()
        if normalized_id in {"invalid", "unknown", "none", "null"}:
            raise KeyError(f"Customer profile '{customer_id}' was not found in the JPMC Core Account Ledger.")

        card_info = DEFAULT_CUSTOMER.get("active_card")
        if not card_info:
            raise RuntimeError("Active card record missing from customer ledger profile.")

        logger.info(
            "account_statement_retrieved",
            tool_name="fetch_live_account_statement",
            customer_id=customer_id,
            masked_pan="************4821",
            status="SUCCESS",
        )
        return {
            "status": "SUCCESS",
            "customer_id": customer_id,
            "account_name": "Chase Sapphire Preferred® Credit Card",
            "account_number": "************4821",
            "credit_limit": card_info["credit_limit"],
            "available_credit": card_info["available_credit"],
            "current_balance": card_info["current_balance"],
            "payment_due_date": "2026-10-25",
            "minimum_payment": 45.00,
            "recent_transactions": [
                {
                    "tx_id": "tx-chi-1000",
                    "date": "2026-09-07T09:14:00Z",
                    "merchant": "Chicago Luxury Electronics",
                    "amount": 1000.00,
                    "city": "Chicago, IL",
                    "status": "PENDING_DISPUTED",
                    "flagged_fraud": True,
                    "note": "Triggered geo-velocity alert against concurrent NY login",
                },
                {
                    "tx_id": "tx-ny-142",
                    "date": "2026-09-07T14:30:00Z",
                    "merchant": "Target Store #1142",
                    "amount": 142.50,
                    "city": "New York, NY",
                    "status": "DECLINED_RESTRICTED",
                    "flagged_fraud": False,
                    "note": "Declined because card was under automated security lock",
                },
                {
                    "tx_id": "tx-lon-42",
                    "date": "2026-09-05T12:15:00Z",
                    "merchant": "Pret A Manger Strand",
                    "amount": 14.80,
                    "city": "London, UK",
                    "status": "POSTED",
                    "flagged_fraud": False,
                    "note": "Authorized under registered international travel notice",
                },
            ],
        }
    except (ValueError, KeyError) as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="fetch_live_account_statement",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="get_card_status",
        )
        return ToolErrorRecoveryResponse(
            tool_name="fetch_live_account_statement",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="get_card_status",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Verify that 'customer_id' is set to the active session customer "
                "('alex_morgan') and retry `fetch_live_account_statement(customer_id='alex_morgan')`. "
                "If ledger lookup remains unavailable, invoke `get_card_status(card_last4='4821')` "
                "to inspect card state from the card processor cache."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="fetch_live_account_statement",
            error_type="LedgerServiceException",
            error=str(exc),
            fallback_tool="query_fraud_velocity_alerts",
        )
        return ToolErrorRecoveryResponse(
            tool_name="fetch_live_account_statement",
            error_type="LedgerServiceException",
            error_message=str(exc),
            retryable=True,
            fallback_tool="query_fraud_velocity_alerts",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Core ledger experienced a transient error. Do not crash or expose "
                "raw stack traces to the customer. Fall back to `get_card_status` and `query_fraud_velocity_alerts` "
                "to synthesize the customer's account state from preloaded Memory Bank context."
            ),
        ).model_dump()


def get_card_status(card_last4: str = "4821") -> Dict[str, Any]:
    """Retrieves real-time restriction and lock status of a card product.

    Includes guided error handling that returns actionable recovery instructions to the LLM
    if a malformed or unrecognized 4-digit card suffix is supplied.

    Args:
        card_last4: The last 4 digits of the card (default '4821').

    Returns:
        Status details, restriction type, and associated digital wallet tokens, or a
        ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        cleaned_last4 = str(card_last4).strip().lstrip("*")
        if not cleaned_last4.isdigit() or len(cleaned_last4) != 4:
            raise ValueError(
                f"Invalid card_last4 '{card_last4}'. Expected exactly 4 numeric digits (e.g., '4821')."
            )

        card = DEFAULT_CUSTOMER["active_card"]
        logger.info(
            "card_status_checked",
            tool_name="get_card_status",
            card_last4=cleaned_last4,
            card_status=card["status"],
        )
        return {
            "status_code": "SUCCESS",
            "card_product": card["product"],
            "masked_pan": card["masked_pan"],
            "last4": cleaned_last4,
            "status": card["status"],
            "lock_reason": card["lock_reason"],
            "digital_wallet_tokens": card["digital_wallet_tokens"],
            "card_replacement_eligible": True,
            "instant_vcn_eligible": True,
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="get_card_status",
            error_type="InvalidCardLast4Format",
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="get_card_status",
            error_type="InvalidCardLast4Format",
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Strip any non-numeric characters or asterisks and pass a 4-digit string "
                "(default active card is '4821'). Retry `get_card_status(card_last4='4821')`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="get_card_status",
            error_type=type(exc).__name__,
            error=str(exc),
            fallback_tool="fetch_live_account_statement",
        )
        return ToolErrorRecoveryResponse(
            tool_name="get_card_status",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="fetch_live_account_statement",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Card status service encountered an unexpected error. Fall back to "
                "`fetch_live_account_statement(customer_id='alex_morgan')` to verify card status."
            ),
        ).model_dump()

