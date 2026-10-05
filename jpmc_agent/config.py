"""Configuration module for JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Mitigation Agent."""

import os
from typing import Dict, Any

# Primary Model Configuration
DEFAULT_MODEL = os.getenv("JPMC_AGENT_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = "gemini-3.5-flash"
GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "jpmc-consumer-credit-sandbox")
GCP_REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")

# Vertex AI Agent Platform & Memory Bank Resource Config
MEMORY_BANK_RESOURCE = os.getenv(
    "VERTEX_MEMORY_BANK_RESOURCE",
    f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/reasoningEngines/959117511771/memories",
)
KNOWLEDGE_CATALOG_CORPUS = os.getenv(
    "KNOWLEDGE_CATALOG_CORPUS",
    f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/ragCorpora/jpmc-cardholder-protection-v1",
)

# Benchmark Rubric Pillars (Maximum Total Score: 95)
EVALUATION_RUBRIC: Dict[str, Dict[str, Any]] = {
    "tool_interface_design": {
        "max_score": 19,
        "name": "Tool & Interface Design",
        "weight": 0.20,
    },
    "context_memory": {
        "max_score": 19,
        "name": "Context & Memory",
        "weight": 0.20,
    },
    "orchestration_logic": {
        "max_score": 19,
        "name": "Orchestration & Logic",
        "weight": 0.20,
    },
    "observability_tracing": {
        "max_score": 19,
        "name": "Observability & Tracing",
        "weight": 0.20,
    },
    "infrastructure_cicd": {
        "max_score": 19,
        "name": "Infrastructure & CI/CD",
        "weight": 0.20,
    },
}

TOTAL_MAX_SCORE = sum(item["max_score"] for item in EVALUATION_RUBRIC.values())  # 95

# Default Customer Profile (Alex Morgan)
DEFAULT_CUSTOMER = {
    "customer_id": "alex_morgan",
    "full_name": "Alex Morgan",
    "tier": "Sapphire Reserve / Preferred Tier",
    "phone": "+1 (555) 234-8901",
    "email": "alex.morgan@example.com",
    "home_address": "450 Lexington Ave, New York, NY 10017",
    "current_travel_location": "The Savoy Hotel, Strand, London WC2R 0EZ, United Kingdom",
    "active_card": {
        "card_id": "card-4821",
        "product": "Chase Sapphire Preferred®",
        "masked_pan": "************4821",
        "last4": "4821",
        "exp": "08/28",
        "status": "SECURITY_LOCKED",
        "lock_reason": "Dual-City Login Geo-Velocity Anomaly & Unsettled Step-Up Auth",
        "credit_limit": 25000.00,
        "available_credit": 21857.50,
        "current_balance": 3142.50,
        "digital_wallet_tokens": [
            {
                "token_id": "tok-apple-pay-01",
                "device": "iPhone 16 Pro (Alex's Phone)",
                "status": "RESTRICTED",
                "wallet_type": "Apple Pay",
            }
        ],
    },
}
