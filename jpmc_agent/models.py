"""Pydantic data models for JPMC Credit Card Replacement & Fraud Mitigation Agent."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class MemoryFragment(BaseModel):
    """Discrete multi-session memory entry stored in Vertex AI Memory Bank."""
    fragment_id: str
    customer_id: str
    channel: str  # FRAUD_DETECTION, TELEPHONY_IVR, MOBILE_APP, WEB_PORTAL, BRANCH_SUPPORT
    day_label: str
    timestamp: str
    summary: str
    severity: str = "INFO"  # INFO, WARNING, HIGH, CRITICAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_compacted_summary: bool = False
    veracity_evaluation: Optional[Dict[str, Any]] = None


class VeracityEvaluation(BaseModel):
    """Pre-write claim veracity validation assessment evaluated across 5 avenues."""
    claim_id: str
    claim_text: str
    veracity_status: str  # VERIFIED_TRUE, CONTRADICTED_BY_TELEMETRY, UNVERIFIED_PENDING
    confidence_score: float = Field(ge=0.0, le=1.0)
    relevant_avenues_checked: List[str]
    corroborating_telemetry: List[str]
    discrepancy_details: Optional[str] = None
    recommended_remediation: Optional[str] = None
    validation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    multi_avenue_audit: Dict[str, Any] = Field(default_factory=dict)


class VirtualCardNumber(BaseModel):
    """Instantly provisioned digital virtual card number (VCN)."""
    vcn_id: str
    card_product: str = "Chase Sapphire Preferred® Digital VCN"
    masked_pan: str
    last4: str
    exp_month_year: str
    cvv: str
    status: str = "ACTIVE_PROVISIONED"
    push_to_apple_wallet_ready: bool = True
    push_to_google_wallet_ready: bool = True
    provisioned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    spending_limit: float = 10000.00


class CourierShipment(BaseModel):
    """Emergency replacement card express delivery logistics."""
    tracking_number: str
    carrier: str = "FedEx Priority International Express"
    service_level: str = "Next-Flight-Out Emergency Courier (Within 24 Hours)"
    destination_address: str
    recipient_name: str
    estimated_delivery: str
    status: str = "DISPATCHED_TO_COURIER"


class OneClickResolutionResult(BaseModel):
    """Consolidated atomic resolution executed by the agent."""
    customer_id: str
    resolution_status: str = "SUCCESS"
    old_card_action: str = "PERMANENTLY_REVOKED_AND_BLOCKED"
    disputed_transactions: List[Dict[str, Any]]
    virtual_card: VirtualCardNumber
    emergency_courier: CourierShipment
    updated_billers_notified: List[str]
    audit_trace_id: str
    summary_message: str


class AuditTraceSpan(BaseModel):
    """OpenTelemetry-compliant structured audit event."""
    trace_id: str
    span_id: str
    agent_name: str
    action_type: str  # PRELOAD_MEMORY, VERACITY_AUDIT, TOOL_EXECUTION, SYNTHESIS, COMPACTION
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    latency_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)
