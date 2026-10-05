"""JPMorgan Chase Instant Cross-Channel Credit Card Replacement & Fraud Mitigation Agent Package.

Exports root_agent for the Google Agent Development Kit (ADK) loader.
"""

from .agent import (
    root_agent,
    fraud_monitoring_agent,
    channel_telemetry_agent,
    claim_veracity_validator_agent,
    card_replacement_logistics_agent,
    GLOBAL_TELEMETRY_SPANS,
)
from .memory.memory_bank import memory_bank_store
from .memory.dreaming_service import DreamingCompactionService
from .config import DEFAULT_CUSTOMER, EVALUATION_RUBRIC, TOTAL_MAX_SCORE

__all__ = [
    "root_agent",
    "fraud_monitoring_agent",
    "channel_telemetry_agent",
    "claim_veracity_validator_agent",
    "card_replacement_logistics_agent",
    "memory_bank_store",
    "DreamingCompactionService",
    "DEFAULT_CUSTOMER",
    "EVALUATION_RUBRIC",
    "TOTAL_MAX_SCORE",
    "GLOBAL_TELEMETRY_SPANS",
]
