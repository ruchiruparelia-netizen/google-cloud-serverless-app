"""Vertex AI Memory Bank client and in-memory persistence layer for JPMC Cross-Channel Agent."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..models import MemoryFragment
from ..config import DEFAULT_CUSTOMER


class ScaleMemoryBank:
    """Manages multi-session cross-channel episodic memory for consumer banking customers.
    
    Adheres to the Google Cloud Vertex AI Memory Bank architecture:
    - Decoupled asynchronous ingestion
    - Pre-write claim veracity linking
    - Preload memory injection at turn start
    - Tokenomic compaction via background Dreaming Service
    """

    def __init__(self):
        self._storage: Dict[str, List[MemoryFragment]] = {}
        self.seed_defaults()

    def seed_defaults(self):
        """Seeds the standard cross-channel scenario for Alex Morgan (*4821)."""
        alex_fragments = [
            MemoryFragment(
                fragment_id="mem-fraud-01",
                customer_id="alex_morgan",
                channel="FRAUD_DETECTION",
                day_label="Day 1 • 09:15 UTC",
                timestamp="2026-09-07T09:15:00Z",
                severity="HIGH",
                summary="FRAUD VELOCITY & STEP-UP ALERT: Concurrent session logins detected from New York, NY (IP 198.51.100.4) and Chicago, IL (IP 203.0.113.19) within 9 minutes. Followed by $1,000.00 POS charge attempt at Chicago Luxury Electronics (initial decline; retry triggered SMS 'Y' step-up). Automated containment placed Chase Sapphire Preferred (*4821) on SECURITY_LOCKED.",
                metadata={
                    "action": "LOCK_CARD",
                    "affected_card": "Chase Sapphire Preferred (*4821)",
                    "risk_score": 92,
                    "locations": ["New York, NY", "Chicago, IL"],
                    "source_system": "RiskOps & Fraud Velocity Engine",
                    "trigger": "Geo-Velocity Mismatch + Step-Up Audit Flag",
                },
                veracity_evaluation={
                    "claim_id": "clm-seed-01",
                    "claim_text": "System-initiated concurrent login alert & $1,000 Chicago step-up.",
                    "veracity_status": "VERIFIED_TRUE",
                    "confidence_score": 0.99,
                    "corroborating_telemetry": [
                        "IP 198.51.100.4 (NY MacBook)",
                        "IP 203.0.113.19 (Chicago Windows/SMS)",
                        "POS Charge $1,000.00 @ Chicago Luxury Electronics",
                    ],
                },
            ),
            MemoryFragment(
                fragment_id="mem-ivr-02",
                customer_id="alex_morgan",
                channel="TELEPHONY_IVR",
                day_label="Day 1 • 14:32 UTC",
                timestamp="2026-09-07T14:32:00Z",
                severity="WARNING",
                summary="TELEPHONY INBOUND CALL & DISCONNECT: Customer dialed inbound IVR after card decline for $142.50 at Target Store #1142 (New York, NY). Automated IVR prompted for 2FA SMS one-time passcode verification, but telephony session abruptly disconnected prior to OTP submission. Card lock restriction remained active.",
                metadata={
                    "channel_session_id": "ivr-sess-99412",
                    "declined_amount": 142.50,
                    "merchant": "Target Store #1142 (New York, NY)",
                    "step_up_status": "DISCONNECTED_BEFORE_COMPLETION",
                    "call_duration_seconds": 78,
                },
                veracity_evaluation={
                    "claim_id": "clm-seed-02",
                    "claim_text": "Customer called IVR after Target decline; call dropped.",
                    "veracity_status": "VERIFIED_TRUE",
                    "confidence_score": 0.98,
                    "corroborating_telemetry": [
                        "Telephony CDR (Call Detail Record) #ivr-sess-99412",
                        "POS Decline Auth Record $142.50 Target #1142",
                    ],
                },
            ),
            MemoryFragment(
                fragment_id="mem-mobile-03",
                customer_id="alex_morgan",
                channel="MOBILE_APP",
                day_label="Day 2 • 11:20 UTC",
                timestamp="2026-09-08T11:20:00Z",
                severity="WARNING",
                summary="MOBILE DIGITAL WALLET RESTRICTION: Customer attempted in-app push-provisioning of Chase Sapphire Preferred (*4821) to Apple Wallet on iPhone 16 Pro. Operation rejected by token vault gateway with error CARD_STATUS_LOCKED_RESTRICTED due to unresolved security lock.",
                metadata={
                    "device": "iPhone 16 Pro (iOS 18.2)",
                    "action_attempted": "Apple Pay Token Push-Provisioning",
                    "gateway_error_code": "CARD_STATUS_LOCKED_RESTRICTED",
                    "device_binding": "tok-apple-pay-01",
                },
                veracity_evaluation={
                    "claim_id": "clm-seed-03",
                    "claim_text": "Customer attempted Apple Pay setup and received restricted error.",
                    "veracity_status": "VERIFIED_TRUE",
                    "confidence_score": 0.97,
                    "corroborating_telemetry": [
                        "Mobile Gateway Session #mob-token-7712",
                        "Token Vault Rejection CARD_STATUS_LOCKED_RESTRICTED",
                    ],
                },
            ),
            MemoryFragment(
                fragment_id="mem-travel-04",
                customer_id="alex_morgan",
                channel="TRAVEL_REGISTRY",
                day_label="Day 0 • Registered Notice",
                timestamp="2026-09-05T18:00:00Z",
                severity="INFO",
                summary="ACTIVE TRAVEL NOTICE: Registered travel window to London, United Kingdom (Sep 28 - Oct 12). Verified temporary lodging address: The Savoy Hotel, Strand, London WC2R 0EZ, United Kingdom. Preferred overseas contact method: Primary Mobile +1 (555) 234-8901.",
                metadata={
                    "destination": "London, United Kingdom",
                    "hotel_address": "The Savoy Hotel, Strand, London WC2R 0EZ, United Kingdom",
                    "window": "2026-09-28 to 2026-10-12",
                    "registered_via": "Chase Mobile App Notice",
                },
                veracity_evaluation={
                    "claim_id": "clm-seed-04",
                    "claim_text": "Customer has verified international travel notice to London.",
                    "veracity_status": "VERIFIED_TRUE",
                    "confidence_score": 1.0,
                    "corroborating_telemetry": [
                        "Travel Notice Registry Entry #TRV-88291-UK",
                        "Verified Mobile App Confirmation",
                    ],
                },
            ),
        ]
        self._storage["alex_morgan"] = alex_fragments

    def get_memories(self, customer_id: str) -> List[MemoryFragment]:
        """Returns all memory fragments for a given customer."""
        return self._storage.get(customer_id, [])

    def add_fragment(self, fragment: MemoryFragment) -> MemoryFragment:
        """Appends a new verified memory fragment."""
        if fragment.customer_id not in self._storage:
            self._storage[fragment.customer_id] = []
        self._storage[fragment.customer_id].append(fragment)
        return fragment

    def search(self, customer_id: str, query: str) -> List[MemoryFragment]:
        """Performs semantic/keyword lookup over customer memories."""
        memories = self.get_memories(customer_id)
        q = query.lower()
        results = []
        for m in memories:
            if (
                q in m.summary.lower()
                or q in m.channel.lower()
                or any(q in str(v).lower() for v in m.metadata.values())
            ):
                results.append(m)
        return results if results else memories

    def generate_preload_context(self, customer_id: str) -> str:
        """Synthesizes memory into a zero-latency working context for root agent turn start."""
        memories = self.get_memories(customer_id)
        if not memories:
            return "No historical cross-channel memories on file."

        lines = [
            f"=== VERTEX AI MEMORY BANK PRELOAD (Customer: {customer_id}) ===",
            f"Active Card: {DEFAULT_CUSTOMER['active_card']['product']} (*4821) | Current Status: {DEFAULT_CUSTOMER['active_card']['status']}",
            f"Lodging / Overseas Address: {DEFAULT_CUSTOMER['current_travel_location']}",
            "Cross-Channel Chronological Memory Fragments:",
        ]
        for m in memories:
            veracity = (
                f"[Veracity: {m.veracity_evaluation.get('veracity_status')} (Conf: {int(m.veracity_evaluation.get('confidence_score', 1)*100)}%)]"
                if m.veracity_evaluation
                else "[Veracity: Unverified]"
            )
            compact_tag = " [COMPACTED SUMMARY]" if m.is_compacted_summary else ""
            lines.append(f"- [{m.day_label}] [{m.channel}]{compact_tag} {veracity}: {m.summary}")

        lines.append("=== END MEMORY BANK PRELOAD ===")
        return "\n".join(lines)


# Singleton Memory Bank instance
memory_bank_store = ScaleMemoryBank()
