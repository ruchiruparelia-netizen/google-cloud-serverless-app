"""Account, core ledger, and card status tools for JPMC Agent."""

from typing import Dict, Any, List
from ..config import DEFAULT_CUSTOMER


def fetch_live_account_statement(customer_id: str = "alex_morgan") -> Dict[str, Any]:
    """Retrieves real-time account ledger statement, pending authorizations, and current balances.
    
    Args:
        customer_id: The unique identifier of the customer (defaults to alex_morgan).
        
    Returns:
        A dictionary containing core banking ledger details, current balance, and recent transactions.
    """
    return {
        "customer_id": customer_id,
        "account_name": "Chase Sapphire Preferred® Credit Card",
        "account_number": "************4821",
        "credit_limit": DEFAULT_CUSTOMER["active_card"]["credit_limit"],
        "available_credit": DEFAULT_CUSTOMER["active_card"]["available_credit"],
        "current_balance": DEFAULT_CUSTOMER["active_card"]["current_balance"],
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


def get_card_status(card_last4: str = "4821") -> Dict[str, Any]:
    """Retrieves real-time restriction and lock status of a card product.
    
    Args:
        card_last4: The last 4 digits of the card (default 4821).
        
    Returns:
        Status details, restriction type, and associated digital wallet tokens.
    """
    card = DEFAULT_CUSTOMER["active_card"]
    return {
        "card_product": card["product"],
        "masked_pan": card["masked_pan"],
        "status": card["status"],
        "lock_reason": card["lock_reason"],
        "digital_wallet_tokens": card["digital_wallet_tokens"],
        "card_replacement_eligible": True,
        "instant_vcn_eligible": True,
    }
