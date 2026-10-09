"""Card operations, instant VCN issuance, and emergency courier logistics tools for JPMC Agent."""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from ..models import (
    VirtualCardNumber,
    CourierShipment,
    OneClickResolutionResult,
    ToolErrorRecoveryResponse,
    HumanInTheLoopInterrupt,
)
from ..config import DEFAULT_CUSTOMER, HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD
from .fraud_tools import file_fraud_dispute

logger = logging.getLogger("jpmc_agent.tools.card_ops")


def request_human_in_the_loop_approval(
    action_name: str,
    customer_id: str = "alex_morgan",
    reason: str = "High-stakes permanent card revocation or high-value credit limit override.",
    proposed_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Programmatically pauses autonomous execution and requests explicit Human-in-the-Loop (HITL) approval.

    Use this tool whenever a high-stakes action requires explicit customer or supervisor sign-off
    before state mutation (e.g., permanent account closure, unverified shipping address, or credit line increase).

    Args:
        action_name: Name of the high-stakes tool or operation requiring approval.
        customer_id: The customer identifier.
        reason: Explanation of why human approval is required.
        proposed_parameters: Dictionary of parameters awaiting human verification.

    Returns:
        Structured HumanInTheLoopInterrupt payload with confirmation token instructions,
        or a ToolErrorRecoveryResponse on error.
    """
    try:
        if not action_name or not str(action_name).strip():
            raise ValueError("action_name must be specified when requesting HITL approval.")

        return HumanInTheLoopInterrupt(
            interrupt_id=f"hitl-req-{uuid.uuid4().hex[:8]}",
            action_name=action_name,
            risk_level="HIGH_STAKES_BANKING_MUTATION",
            reason=reason,
            proposed_arguments=proposed_parameters or {"customer_id": customer_id},
            approval_instructions=(
                "Present the proposed action details clearly to the human user/supervisor. "
                "Wait for explicit confirmation ('Yes, I approve') before invoking the target tool with `human_approved=True`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.warning("Error in request_human_in_the_loop_approval: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="request_human_in_the_loop_approval",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Provide a non-empty `action_name` string (e.g. "
                "'execute_one_click_card_unlock_and_replacement') and retry."
            ),
        ).model_dump()


def provision_instant_virtual_card(
    customer_id: str = "alex_morgan",
    card_product: str = "Chase Sapphire Preferred®",
    spending_limit: float = 10000.00,
    human_approved: bool = True,
    hitl_confirmation_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Instantly provisions an active Digital Virtual Card Number (VCN) for Apple Pay and Google Wallet.

    Includes programmatic HITL code stop for spending limits exceeding HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD
    ($25,000.00) and guided try-except error recovery instructions for the LLM.

    Args:
        customer_id: The customer identifier.
        card_product: The product name of the card.
        spending_limit: Temporary credit line limit on the virtual token (must be > 0).
        human_approved: Whether human approval has been granted for provisioning.
        hitl_confirmation_token: Optional supervisor token for high spending limits.

    Returns:
        Virtual card details, masked PAN, expiration, CVV, and mobile wallet push readiness,
        or a HumanInTheLoopInterrupt / ToolErrorRecoveryResponse dictionary.
    """
    try:
        if not customer_id or not str(customer_id).strip():
            raise ValueError("customer_id must be a non-empty string.")
        if spending_limit is None or float(spending_limit) <= 0:
            raise ValueError(f"spending_limit must be > 0 (received: {spending_limit}).")

        numeric_limit = float(spending_limit)

        # PROGRAMMATIC HUMAN-IN-THE-LOOP (HITL) CODE STOP
        if not human_approved or (
            numeric_limit > HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD and not hitl_confirmation_token
        ):
            return HumanInTheLoopInterrupt(
                interrupt_id=f"hitl-vcn-{uuid.uuid4().hex[:8]}",
                action_name="provision_instant_virtual_card",
                risk_level="HIGH_CREDIT_LINE_EXPOSURE",
                reason=(
                    f"Requested VCN spending limit (${numeric_limit:,.2f}) exceeds autonomous threshold "
                    f"(${HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD:,.2f}) or lacks explicit human confirmation."
                ),
                proposed_arguments={
                    "customer_id": customer_id,
                    "card_product": card_product,
                    "spending_limit": numeric_limit,
                },
                approval_instructions=(
                    "Request human confirmation or reduce `spending_limit` to <= $25,000.00 before retrying."
                ),
            ).model_dump()

        vcn_last4 = "9183"
        vcn = VirtualCardNumber(
            vcn_id=f"vcn-{uuid.uuid4().hex[:8]}",
            card_product=f"{card_product} Digital VCN",
            masked_pan=f"************{vcn_last4}",
            last4=vcn_last4,
            exp_month_year="09/29",
            cvv="419",
            status="ACTIVE_PROVISIONED",
            push_to_apple_wallet_ready=True,
            push_to_google_wallet_ready=True,
            spending_limit=numeric_limit,
        )
        return vcn.model_dump()
    except (ValueError, TypeError) as exc:
        logger.warning("Validation error in provision_instant_virtual_card: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="provision_instant_virtual_card",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="get_card_status",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Ensure `customer_id='alex_morgan'` and `spending_limit` is a positive "
                "float between 100.00 and 25000.00 (default 10000.00), then retry `provision_instant_virtual_card`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error("Unexpected error in provision_instant_virtual_card: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="provision_instant_virtual_card",
            error_type="TokenizationGatewayException",
            error_message=str(exc),
            retryable=True,
            fallback_tool="dispatch_emergency_courier",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Digital VCN tokenization encountered a transient error. Retry "
                "`provision_instant_virtual_card` or proceed with `dispatch_emergency_courier` so physical "
                "card delivery is not delayed."
            ),
        ).model_dump()


def dispatch_emergency_courier(
    customer_id: str = "alex_morgan",
    destination_address: Optional[str] = None,
    recipient_name: Optional[str] = None,
    human_approved: bool = True,
) -> Dict[str, Any]:
    """Dispatches a replacement physical contactless card via emergency international priority courier.

    Includes programmatic HITL verification and guided try-except error recovery instructions for the LLM.

    Args:
        customer_id: The customer identifier.
        destination_address: The delivery address (defaults to current travel location/hotel).
        recipient_name: Recipient full name.
        human_approved: Whether human confirmation has been received for physical card dispatch.

    Returns:
        Courier tracking details, carrier, estimated arrival timestamp, and delivery SLA,
        or a HumanInTheLoopInterrupt / ToolErrorRecoveryResponse dictionary.
    """
    try:
        if not customer_id or not str(customer_id).strip():
            raise ValueError("customer_id must be a non-empty string.")

        if not human_approved:
            return HumanInTheLoopInterrupt(
                interrupt_id=f"hitl-ship-{uuid.uuid4().hex[:8]}",
                action_name="dispatch_emergency_courier",
                risk_level="INTERNATIONAL_PHYSICAL_CARD_DISPATCH",
                reason="Physical replacement card international courier dispatch requires customer confirmation.",
                proposed_arguments={
                    "customer_id": customer_id,
                    "destination_address": destination_address or DEFAULT_CUSTOMER["current_travel_location"],
                },
                approval_instructions=(
                    "Confirm the hotel delivery address with the customer and re-invoke with `human_approved=True`."
                ),
            ).model_dump()

        dest = (destination_address or DEFAULT_CUSTOMER["current_travel_location"]).strip()
        if len(dest) < 5:
            raise ValueError(f"Destination address '{dest}' is too short or incomplete for international courier.")

        name = (recipient_name or DEFAULT_CUSTOMER["full_name"]).strip()
        est_delivery = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%A, %b %d at 2:00 PM GMT")

        shipment = CourierShipment(
            tracking_number=f"7894{uuid.uuid4().hex[:8].upper()}",
            carrier="FedEx Priority International Express",
            service_level="Next-Flight-Out Emergency Courier (Within 24 Hours)",
            destination_address=dest,
            recipient_name=name,
            estimated_delivery=est_delivery,
            status="DISPATCHED_TO_COURIER",
        )
        return shipment.model_dump()
    except ValueError as exc:
        logger.warning("Address validation error in dispatch_emergency_courier: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="dispatch_emergency_courier",
            error_type="InvalidShippingAddress",
            error_message=str(exc),
            retryable=True,
            fallback_tool="query_travel_registry",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Call `query_travel_registry(customer_id='alex_morgan')` to retrieve the "
                "customer's verified hotel lodging address ('The Savoy Hotel, Strand, London WC2R 0EZ, United Kingdom'), "
                "or omit `destination_address` to use the verified travel registry address automatically."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error("Unexpected error in dispatch_emergency_courier: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="dispatch_emergency_courier",
            error_type="CourierLogisticsException",
            error_message=str(exc),
            retryable=True,
            fallback_tool="provision_instant_virtual_card",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Courier dispatch gateway encountered an error. Ensure the customer has an active "
                "Digital VCN via `provision_instant_virtual_card` first, then retry `dispatch_emergency_courier`."
            ),
        ).model_dump()


def execute_one_click_card_unlock_and_replacement(
    customer_id: str = "alex_morgan",
    dispute_fraudulent_transactions: bool = True,
    destination_address: Optional[str] = None,
    human_approved: bool = True,
    hitl_confirmation_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes atomic 1-click cross-channel resolution: blocks compromised card, provisions instant VCN, and dispatches courier.

    This consolidated high-stakes tool performs all essential fraud mitigation and card replacement actions
    in a single atomic flow, protected by a programmatic Human-in-the-Loop (HITL) code stop (`human_approved`)
    and comprehensive try-except error recovery instructions:
      1. Permanently revokes compromised physical card (*4821) and suspends compromised tokens.
      2. Auto-files a dispute for the $1,000 fraudulent Chicago charge and credits the account.
      3. Instantly provisions a new Digital Virtual Card Number (VCN) with Apple Pay / Google Wallet push integration.
      4. Dispatches a physical contactless replacement card via emergency priority courier to the customer's hotel.
      5. Automatically notifies registered recurring billers (Netflix, Spotify, transit) with the new VCN.

    Args:
        customer_id: The customer identifier.
        dispute_fraudulent_transactions: Whether to file provisional credit disputes for flagged charges.
        destination_address: Shipping address for the emergency replacement card.
        human_approved: Programmatic HITL gate flag; if False, halts irreversible card revocation until confirmed.
        hitl_confirmation_token: Optional confirmation token from human-in-the-loop approval flow.

    Returns:
        Consolidated OneClickResolutionResult containing all generated assets and confirmations,
        or a HumanInTheLoopInterrupt / ToolErrorRecoveryResponse dictionary.
    """
    try:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("customer_id must be a non-empty string.")

        # PROGRAMMATIC HUMAN-IN-THE-LOOP (HITL) CODE STOP FOR IRREVERSIBLE CARD REVOCATION
        if not human_approved:
            logger.info("Programmatic HITL Code Stop triggered on execute_one_click_card_unlock_and_replacement")
            return HumanInTheLoopInterrupt(
                interrupt_id=f"hitl-1click-{uuid.uuid4().hex[:8]}",
                action_name="execute_one_click_card_unlock_and_replacement",
                risk_level="IRREVERSIBLE_CARD_REVOCATION_AND_CREDIT",
                reason=(
                    "Permanent deactivation of physical card *4821, $1,000.00 provisional credit issuance, "
                    "and international courier dispatch require explicit customer/human confirmation."
                ),
                proposed_arguments={
                    "customer_id": customer_id,
                    "dispute_fraudulent_transactions": dispute_fraudulent_transactions,
                    "destination_address": destination_address or DEFAULT_CUSTOMER["current_travel_location"],
                },
                approval_instructions=(
                    "Ask the customer to confirm ('Would you like me to proceed with this instant resolution?') "
                    "and upon confirmation re-invoke `execute_one_click_card_unlock_and_replacement` with `human_approved=True`."
                ),
            ).model_dump()

        # 1. Dispute the fraudulent transaction
        disputes = []
        if dispute_fraudulent_transactions:
            disp = file_fraud_dispute(
                transaction_id="tx-chi-1000",
                amount=1000.00,
                merchant="Chicago Luxury Electronics",
                dispute_reason="UNAUTHORIZED_GEO_VELOCITY_FRAUD",
                human_approved=True,
                hitl_confirmation_token=hitl_confirmation_token,
            )
            disputes.append(disp)

        # 2. Provision instant VCN
        vcn_data = provision_instant_virtual_card(customer_id=customer_id, human_approved=True)
        if vcn_data.get("status") == "ERROR":
            raise RuntimeError(f"VCN provisioning step failed: {vcn_data.get('error_message')}")

        # 3. Dispatch emergency courier
        courier_data = dispatch_emergency_courier(
            customer_id=customer_id,
            destination_address=destination_address or DEFAULT_CUSTOMER["current_travel_location"],
            human_approved=True,
        )
        if courier_data.get("status") == "ERROR":
            raise RuntimeError(f"Courier dispatch step failed: {courier_data.get('error_message')}")

        # 4. Recurring billers updated via token exchange network
        billers = ["Netflix Subscription", "Spotify Premium", "TfL Transit (London)", "Uber Technologies"]

        audit_trace = f"trace-jpmc-resolve-{uuid.uuid4().hex[:10]}"

        summary = (
            f"Your request has been completely resolved in one step: "
            f"1) Compromised Sapphire Preferred (*4821) is permanently locked and terminated. "
            f"2) Fraud dispute filed for $1,000.00 at Chicago Luxury Electronics with immediate provisional credit posted. "
            f"3) Instant Digital Virtual Card (*{vcn_data['last4']}) is provisioned and ready to push to your Apple Wallet or Google Wallet immediately. "
            f"4) Emergency replacement physical card is dispatched via FedEx Priority International ({courier_data['tracking_number']}) to {courier_data['destination_address']} with expected delivery {courier_data['estimated_delivery']}."
        )

        result = OneClickResolutionResult(
            customer_id=customer_id,
            resolution_status="SUCCESS",
            old_card_action="PERMANENTLY_REVOKED_AND_BLOCKED",
            disputed_transactions=disputes,
            virtual_card=VirtualCardNumber(**vcn_data),
            emergency_courier=CourierShipment(**courier_data),
            updated_billers_notified=billers,
            audit_trace_id=audit_trace,
            summary_message=summary,
        )

        return result.model_dump()
    except (ValueError, RuntimeError) as exc:
        logger.warning("Error in execute_one_click_card_unlock_and_replacement: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="execute_one_click_card_unlock_and_replacement",
            error_type=type(exc).__name__,
            error_message=str(exc),
            retryable=True,
            fallback_tool="provision_instant_virtual_card",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Atomic 1-click resolution encountered a validation or sub-step error. "
                "Verify `customer_id='alex_morgan'` and `destination_address` is valid, or execute the "
                "individual tools sequentially: 1) `file_fraud_dispute`, 2) `provision_instant_virtual_card`, "
                "and 3) `dispatch_emergency_courier`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error("Unexpected failure in execute_one_click_card_unlock_and_replacement: %s", exc)
        return ToolErrorRecoveryResponse(
            tool_name="execute_one_click_card_unlock_and_replacement",
            error_type="AtomicResolutionFailure",
            error_message=str(exc),
            retryable=True,
            fallback_tool="provision_instant_virtual_card",
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Do not crash. Execute fallback modular tools (`provision_instant_virtual_card` "
                "and `dispatch_emergency_courier`) to ensure customer continuity."
            ),
        ).model_dump()

