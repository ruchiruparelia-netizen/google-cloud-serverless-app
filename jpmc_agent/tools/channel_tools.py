"""Multi-channel telemetry tools for IVR, Mobile App, and Travel Registry."""

from typing import Dict, Any, List
from ..config import DEFAULT_CUSTOMER


def query_telephony_ivr_logs(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Retrieves contact center IVR telephony session details and dropped call logs.
    
    Args:
        customer_id: The customer identifier.
        
    Returns:
        Recent IVR sessions, DTMF inputs, speech recognition logs, and premature disconnection records.
    """
    return {
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


def query_mobile_wallet_events(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Queries mobile app sessions, device bindings, and digital wallet tokenization errors.
    
    Args:
        customer_id: The customer identifier.
        
    Returns:
        Digital wallet token requests, Apple Pay/Google Wallet push events, and error codes.
    """
    return {
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


def query_travel_registry(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Queries verified travel itineraries and international trip notices on file.
    
    Args:
        customer_id: The customer identifier.
        
    Returns:
        Active and upcoming travel destinations, verified hotel/lodging addresses, and travel dates.
    """
    return {
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
