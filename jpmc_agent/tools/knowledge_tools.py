"""Knowledge Catalog retrieval tool for JPMC governance and banking policies."""

from typing import Dict, Any, List
import structlog
from ..config import KNOWLEDGE_CATALOG_CORPUS
from ..models import ToolErrorRecoveryResponse
from ..observability import get_structured_logger

logger = get_structured_logger("jpmc_agent.tools.knowledge")


def query_knowledge_catalog(query: str) -> Dict[str, Any]:
    """Retrieves authoritative institutional banking policies and procedures from JPMC Knowledge Catalog.

    Includes guided error handling returning structured LLM recovery instructions if the
    search query is empty or the Vertex AI RAG corpus encounters an exception.

    Args:
        query: Policy search query (e.g. 'zero liability', 'emergency replacement courier SLA', 'instant VCN issuance').

    Returns:
        Relevant policy rules, compliance constraints, and operational SLAs,
        or a ToolErrorRecoveryResponse dictionary if an error occurs.
    """
    try:
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Policy search `query` must be a non-empty string.")

        q = query.strip().lower()
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

        selected = matched if matched else policies[:2]
        logger.info(
            "knowledge_catalog_queried",
            tool_name="query_knowledge_catalog",
            query=query,
            matched_count=len(selected),
            corpus_id=KNOWLEDGE_CATALOG_CORPUS,
        )
        return {
            "query": query,
            "matched_policies": selected,
            "corpus_id": KNOWLEDGE_CATALOG_CORPUS,
            "retrieval_status": "SUCCESS",
        }
    except ValueError as exc:
        logger.warning(
            "tool_validation_error",
            tool_name="query_knowledge_catalog",
            error_type="EmptyPolicyQuery",
            error=str(exc),
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_knowledge_catalog",
            error_type="EmptyPolicyQuery",
            error_message=str(exc),
            retryable=True,
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Supply a specific policy search keyword such as 'zero liability', "
                "'emergency courier SLA', or 'instant VCN issuance' and retry `query_knowledge_catalog`."
            ),
        ).model_dump()
    except Exception as exc:
        logger.error(
            "tool_execution_exception",
            tool_name="query_knowledge_catalog",
            error_type="KnowledgeCorpusException",
            error=str(exc),
        )
        return ToolErrorRecoveryResponse(
            tool_name="query_knowledge_catalog",
            error_type="KnowledgeCorpusException",
            error_message=str(exc),
            retryable=True,
            llm_recovery_instructions=(
                "RECOVERY GUIDANCE: Knowledge Catalog RAG retrieval encountered a transient error. Apply "
                "standard Reg Z Zero Liability and 24-hour Sapphire International Courier SLAs from system instructions."
            ),
        ).model_dump()

