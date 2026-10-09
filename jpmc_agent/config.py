"""Configuration module for JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Mitigation Agent."""

import os
from typing import Dict, Any

# Strategic Multi-Model Routing Configuration (Cost, Latency & Reasoning Tiering)
# 1. Pro Model: High-complexity causal reasoning, multi-agent synthesis, & 5-avenue veracity gatekeeping
REASONING_PRO_MODEL = os.getenv("JPMC_REASONING_PRO_MODEL", "gemini-2.5-pro")
# 2. Flash Model: Sub-second real-time fraud velocity detection & atomic card replacement execution
FAST_FLASH_MODEL = os.getenv("JPMC_FAST_FLASH_MODEL", "gemini-2.5-flash")
# 3. Flash-Lite Model: High-throughput, low-cost channel telemetry parsing (IVR CDRs, wallet logs)
LITE_TELEMETRY_MODEL = os.getenv("JPMC_LITE_TELEMETRY_MODEL", "gemini-2.5-flash-lite")

DEFAULT_MODEL = os.getenv("JPMC_AGENT_MODEL", REASONING_PRO_MODEL)
FALLBACK_MODEL = FAST_FLASH_MODEL

MODEL_ROUTING_TABLE: Dict[str, str] = {
    "consumer_credit_synthesizer_agent": REASONING_PRO_MODEL,
    "claim_veracity_validator_agent": REASONING_PRO_MODEL,
    "fraud_monitoring_agent": FAST_FLASH_MODEL,
    "card_replacement_logistics_agent": FAST_FLASH_MODEL,
    "channel_telemetry_agent": LITE_TELEMETRY_MODEL,
}

# Human-in-the-Loop (HITL) Programmatic Code Stop Thresholds for High-Stakes Actions
HITL_HIGH_VALUE_DISPUTE_THRESHOLD_USD = float(os.getenv("HITL_DISPUTE_THRESHOLD_USD", "2500.00"))
HITL_HIGH_SPENDING_LIMIT_THRESHOLD_USD = float(os.getenv("HITL_VCN_LIMIT_THRESHOLD_USD", "25000.00"))
HITL_LOW_VERACITY_CONFIDENCE_THRESHOLD = float(os.getenv("HITL_VERACITY_THRESHOLD", "0.80"))

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "ruchi-agent-poc")
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
