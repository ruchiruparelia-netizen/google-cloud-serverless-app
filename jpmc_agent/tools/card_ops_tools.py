"""Card operations, instant VCN issuance, and emergency courier logistics tools for JPMC Agent."""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from ..models import VirtualCardNumber, CourierShipment, OneClickResolutionResult
from ..config import DEFAULT_CUSTOMER
from .fraud_tools import file_fraud_dispute


def provision_instant_virtual_card(
    customer_id: str = "alex_morgan",
    card_product: str = "Chase Sapphire Preferred®",
    spending_limit: float = 10000.00,
) -> Dict[str, Any]:
    """Instantly provisions an active Digital Virtual Card Number (VCN) for Apple Pay and Google Wallet.
    
    Args:
        customer_id: The customer identifier.
        card_product: The product name of the card.
        spending_limit: Temporary credit line limit on the virtual token.
        
    Returns:
        Virtual card details, masked PAN, expiration, CVV, and mobile wallet push readiness.
    """
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
        spending_limit=spending_limit,
    )
    return vcn.model_dump()


def dispatch_emergency_courier(
    customer_id: str = "alex_morgan",
    destination_address: Optional[str] = None,
    recipient_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatches a replacement physical contactless card via emergency international priority courier.
    
    Args:
        customer_id: The customer identifier.
        destination_address: The delivery address (defaults to current travel location/hotel).
        recipient_name: Recipient full name.
        
    Returns:
        Courier tracking details, carrier, estimated arrival timestamp, and delivery SLA.
    """
    dest = destination_address or DEFAULT_CUSTOMER["current_travel_location"]
    name = recipient_name or DEFAULT_CUSTOMER["full_name"]
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


def execute_one_click_card_unlock_and_replacement(
    customer_id: str = "alex_morgan",
    dispute_fraudulent_transactions: bool = True,
    destination_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes atomic 1-click cross-channel resolution: blocks compromised card, provisions instant VCN, and dispatches courier.
    
    This consolidated tool performs all essential fraud mitigation and card replacement actions in a single atomic flow:
      1. Permanently revokes compromised physical card (*4821) and suspends compromised tokens.
      2. Auto-files a dispute for the $1,000 fraudulent Chicago charge and credits the account.
      3. Instantly provisions a new Digital Virtual Card Number (VCN) with Apple Pay / Google Wallet push integration.
      4. Dispatches a physical contactless replacement card via emergency priority courier to the customer's hotel.
      5. Automatically notifies registered recurring billers (Netflix, Spotify, transit) with the new VCN.
      
    Args:
        customer_id: The customer identifier.
        dispute_fraudulent_transactions: Whether to file provisional credit disputes for flagged charges.
        destination_address: Shipping address for the emergency replacement card.
        
    Returns:
        Consolidated OneClickResolutionResult containing all generated assets and confirmations.
    """
    # 1. Dispute the fraudulent transaction
    disputes = []
    if dispute_fraudulent_transactions:
        disp = file_fraud_dispute(
            transaction_id="tx-chi-1000",
            amount=1000.00,
            merchant="Chicago Luxury Electronics",
            dispute_reason="UNAUTHORIZED_GEO_VELOCITY_FRAUD",
        )
        disputes.append(disp)

    # 2. Provision instant VCN
    vcn_data = provision_instant_virtual_card(customer_id=customer_id)

    # 3. Dispatch emergency courier
    courier_data = dispatch_emergency_courier(
        customer_id=customer_id,
        destination_address=destination_address or DEFAULT_CUSTOMER["current_travel_location"],
    )

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
