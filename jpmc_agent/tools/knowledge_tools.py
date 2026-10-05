"""Knowledge Catalog retrieval tool for JPMC governance and banking policies."""

from typing import Dict, Any, List


def query_knowledge_catalog(query: str) -> Dict[str, Any]:
    """Retrieves authoritative institutional banking policies and procedures from JPMC Knowledge Catalog.
    
    Args:
        query: Policy search query (e.g. 'zero liability', 'emergency replacement courier SLA', 'instant VCN issuance').
        
    Returns:
        Relevant policy rules, compliance constraints, and operational SLAs.
    """
    q = query.lower()
    policies = [
        {
            "policy_id": "POL-CCB-ZERO-LIABILITY",
            "title": "JPMorgan Chase Zero Liability Policy for Credit Cards",
            "summary": (
                "Cardholders are 100% protected against unauthorized charges made with their physical card, "
                "digital wallet token, or online card number. When a consumer reports fraudulent transactions or "
                "a lost/stolen card, provisional credit must be granted immediately upon dispute initiation without penalty."
            ),
            "compliance_standard": "Regulation Z (12 CFR Part 1026) & Card Brand Operating Rules",
        },
        {
            "policy_id": "POL-CCB-EMERGENCY-COURIER-SLA",
            "title": "Emergency International Physical Card Reissue & Courier SLA",
            "summary": (
                "For Sapphire Preferred and Sapphire Reserve cardholders traveling internationally who experience "
                "a lost, stolen, or compromised card, Chase provides emergency international courier delivery within "
                "24 to 48 business hours anywhere globally, sent directly to verified hotel lodging or local embassy."
            ),
            "carrier_service": "FedEx / DHL Next-Flight-Out Emergency Courier",
        },
        {
            "policy_id": "POL-CCB-INSTANT-VCN-ISSUANCE",
            "title": "Digital Virtual Card Number (VCN) Push-Provisioning Standard",
            "summary": (
                "To eliminate customer disruption following a card compromise, the agent platform must immediately "
                "provision a digital Virtual Card Number (VCN) with instant push capability to Apple Pay and Google Wallet "
                "prior to physical card manufacturing. The VCN shares the primary credit line and auto-updates recurring billers."
            ),
            "tokenization_spec": "EMV Payment Tokenization Specification v2.3",
        },
        {
            "policy_id": "POL-CCB-VERACITY-GATEWAY",
            "title": "Agent Platform Pre-Write Veracity Gatekeeping Rule",
            "summary": (
                "All customer assertions regarding lost cards, disputed transactions, or travel locations must be "
                "audited against five independent ground-truth telemetry avenues prior to permanent commit to the "
                "Scale Memory Bank to prevent hallucinations, memory poisoning, or social engineering."
            ),
            "security_standard": "Gemini Enterprise Agent Platform Security Assurance Layer",
        },
    ]

    matched = []
    for p in policies:
        if (
            any(w in p["title"].lower() for w in q.split())
            or any(w in p["summary"].lower() for w in q.split())
            or q in p["title"].lower()
        ):
            matched.append(p)

    return {
        "query": query,
        "matched_policies": matched if matched else policies[:2],
        "corpus_id": "projects/jpmc-consumer-credit-sandbox/ragCorpora/jpmc-cardholder-protection-v1",
        "retrieval_status": "SUCCESS",
    }
