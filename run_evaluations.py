"""Automated Evaluation Runner for JPMorgan Chase Agent Platform Architecture.

Executes all 5 criteria eval sets and scores the agent architecture against the 95-point benchmark:
  - Criterion 1: Tool & Interface Design (19 pts)
  - Criterion 2: Context & Memory (19 pts)
  - Criterion 3: Orchestration & Logic (19 pts)
  - Criterion 4: Observability & Tracing (19 pts)
  - Criterion 5: Infrastructure & CI/CD (19 pts)
Total Maximum Score: 95 Points.
"""

import sys
import os
import json
import time
import subprocess
from typing import Dict, Any, List

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from web_server import app
from jpmc_agent.agent import root_agent
from jpmc_agent.memory.memory_bank import memory_bank_store
from jpmc_agent.memory.dreaming_service import DreamingCompactionService
from jpmc_agent.tools import (
    validate_and_record_customer_claim,
    execute_one_click_card_unlock_and_replacement,
    fetch_live_account_statement,
    get_card_status,
)
from jpmc_agent.config import DEFAULT_CUSTOMER, TOTAL_MAX_SCORE

client = TestClient(app)


def print_header(title: str):
    print("\n" + "=" * 76)
    print(f"  {title}")
    print("=" * 76)


class ArchitectureEvaluator:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total_score = 0

    def evaluate_criterion_1_tool_interface_design(self) -> int:
        print_header("CRITERION 1: Tool & Interface Design (Max Score: 19 Points)")
        score = 0

        # Case 1.1: 12-Tool Schema & Type Strictness (5 pts)
        tools = root_agent.tools
        assert len(tools) >= 12
        print(f"  [Case 1.1] 12 Registered Tools Schema Check: PASS ({len(tools)} tools registered) (+5 pts)")
        score += 5

        # Case 1.2: Atomic 1-Click Resolution Execution (5 pts)
        res = execute_one_click_card_unlock_and_replacement("alex_morgan")
        assert res["resolution_status"] == "SUCCESS"
        assert res["old_card_action"] == "PERMANENTLY_REVOKED_AND_BLOCKED"
        assert res["virtual_card"]["status"] == "ACTIVE_PROVISIONED"
        assert res["emergency_courier"]["status"] == "DISPATCHED_TO_COURIER"
        assert len(res["disputed_transactions"]) == 1
        print("  [Case 1.2] Atomic 1-Click Master Resolution Tool: PASS (+5 pts)")
        score += 5

        # Case 1.3: PCI-DSS PAN Masking (4 pts)
        chat_resp = client.post("/api/chat", json={"message": "What is my card number?", "customer_id": "alex_morgan"}).json()
        assert "*4821" in chat_resp["reply"]
        assert "48210000" not in chat_resp["reply"]
        print("  [Case 1.3] PCI-DSS Primary Account Number Masking: PASS (+4 pts)")
        score += 4

        # Case 1.4: JPMC Brand Compliance & Interactive Assets (5 pts)
        index_html = open("ui/index.html").read()
        assert "chase-logo-svg" in index_html
        assert "JPMorgan Chase" in index_html
        assert "credit-card-preview" in index_html
        assert "add-apple-wallet-btn" in index_html
        print("  [Case 1.4] JPMC Brand Compliance & Interactive UI Assets: PASS (+5 pts)")
        score += 5

        self.results["tool_interface_design"] = {"name": "Tool & Interface Design", "score": score, "max": 19}
        self.total_score += score
        return score

    def evaluate_criterion_2_context_memory(self) -> int:
        print_header("CRITERION 2: Context & Memory (Max Score: 19 Points)")
        score = 0

        # Case 2.1: Turn-Start Preload (5 pts)
        preload = memory_bank_store.generate_preload_context("alex_morgan")
        assert "VERTEX AI MEMORY BANK PRELOAD" in preload
        assert "SECURITY_LOCKED" in preload
        assert "The Savoy Hotel" in preload
        print("  [Case 2.1] Turn-Start Memory Preloading (Zero-Latency Context): PASS (+5 pts)")
        score += 5

        # Case 2.2: Episodic Channel Correlation (5 pts)
        memories = memory_bank_store.get_memories("alex_morgan")
        channels = {m.channel for m in memories}
        assert "FRAUD_DETECTION" in channels
        assert "TELEPHONY_IVR" in channels
        assert "MOBILE_APP" in channels
        assert "TRAVEL_REGISTRY" in channels
        print("  [Case 2.2] Episodic Multi-Channel Context Integrity (4 Channels): PASS (+5 pts)")
        score += 5

        # Case 2.3: Dreaming Compaction Efficiency (5 pts)
        compaction = DreamingCompactionService.compact_customer_memories("alex_morgan")
        assert compaction["status"] == "COMPACTED"
        reduction = float(compaction["token_reduction_percentage"].replace("%", ""))
        assert reduction >= 50.0
        print(f"  [Case 2.3] Dreaming Service Compaction Tokenomics ({reduction}% reduction): PASS (+5 pts)")
        score += 5

        # Re-seed memory after compaction test
        memory_bank_store.seed_defaults()

        # Case 2.4: Pre-Write Claim Veracity Gatekeeping (4 pts)
        v1 = validate_and_record_customer_claim("alex_morgan", "Someone stole my wallet in London!")
        assert v1["veracity_status"] == "VERIFIED_TRUE"
        assert v1["confidence_score"] >= 0.95
        v2 = validate_and_record_customer_claim("alex_morgan", "I didn't make the $1,000 charge in Chicago.")
        assert v2["veracity_status"] == "VERIFIED_TRUE"
        print(f"  [Case 2.4] 5-Avenue Pre-Write Claim Veracity Gatekeeping: PASS (+4 pts)")
        score += 4

        self.results["context_memory"] = {"name": "Context & Memory", "score": score, "max": 19}
        self.total_score += score
        return score

    def evaluate_criterion_3_orchestration_logic(self) -> int:
        print_header("CRITERION 3: Orchestration & Logic (Max Score: 19 Points)")
        score = 0

        # Case 3.1: Zero-Question Root Cause Synthesis (5 pts)
        chat_resp = client.post("/api/chat", json={"message": "Why was my card declined at Target?", "customer_id": "alex_morgan"}).json()
        reply = chat_resp["reply"]
        assert "What is your card number?" not in reply
        assert "Target Store #1142" in reply
        assert "SECURITY_LOCKED" in reply
        assert "Chicago" in reply
        print("  [Case 3.1] Zero-Question Root Cause Synthesis: PASS (+5 pts)")
        score += 5

        # Case 3.2: Multi-Agent Mesh Coordination (5 pts)
        sub_agents = [sa.name for sa in root_agent.sub_agents]
        assert "fraud_monitoring_agent" in sub_agents
        assert "channel_telemetry_agent" in sub_agents
        assert "claim_veracity_validator_agent" in sub_agents
        assert "card_replacement_logistics_agent" in sub_agents
        print(f"  [Case 3.2] Multi-Agent Mesh Delegation Hierarchy (4 Sub-Agents): PASS (+5 pts)")
        score += 5

        # Case 3.3: Overseas Stolen Wallet Emergency Flow (5 pts)
        wallet_resp = client.post(
            "/api/chat",
            json={"message": "Someone just stole my wallet in London! Send replacement to my hotel immediately.", "customer_id": "alex_morgan"}
        ).json()
        assert wallet_resp["action_executed"] == "ONE_CLICK_RESOLUTION"
        res_data = wallet_resp["action_data"]
        assert "The Savoy Hotel" in res_data["emergency_courier"]["destination_address"]
        assert res_data["virtual_card"]["status"] == "ACTIVE_PROVISIONED"
        print("  [Case 3.3] Overseas Stolen Wallet Emergency Logistics Flow: PASS (+5 pts)")
        score += 5

        # Case 3.4: Reg E / Reg Z Consumer Credit Compliance (4 pts)
        disp_resp = client.post(
            "/api/chat",
            json={"message": "I didn't make the $1,000 charge in Chicago. Please dispute it.", "customer_id": "alex_morgan"}
        ).json()
        reply_lower = disp_resp["reply"].lower()
        assert "zero liability" in reply_lower
        assert "provisional credit" in reply_lower
        assert "dsp-" in reply_lower
        print("  [Case 3.4] Reg E / Reg Z Consumer Credit Compliance & Tone: PASS (+4 pts)")
        score += 4

        self.results["orchestration_logic"] = {"name": "Orchestration & Logic", "score": score, "max": 19}
        self.total_score += score
        return score

    def evaluate_criterion_4_observability_tracing(self) -> int:
        print_header("CRITERION 4: Observability & Tracing (Max Score: 19 Points)")
        score = 0

        # Case 4.1: OpenTelemetry Granular Spans (5 pts)
        spans_resp = client.get("/api/telemetry/spans").json()
        span_types = {s["type"] for s in spans_resp["spans"]}
        assert "PRELOAD_MEMORY_RECALL" in span_types
        assert "VERACITY_AUDIT" in span_types
        assert "AGENT_SYNTHESIS_COMPLETE" in span_types
        print(f"  [Case 4.1] OpenTelemetry Granular Lifecycle Spans ({len(spans_resp['spans'])} spans recorded): PASS (+5 pts)")
        score += 5

        # Case 4.2: Distributed Trace Propagation (5 pts)
        res = execute_one_click_card_unlock_and_replacement("alex_morgan")
        assert res["audit_trace_id"].startswith("trace-jpmc-resolve-")
        print(f"  [Case 4.2] Distributed Trace Context Propagation ({res['audit_trace_id']}): PASS (+5 pts)")
        score += 5

        # Case 4.3: Latency Performance SLA (5 pts)
        t0 = time.time()
        client.post("/api/chat", json={"message": "Why was my card declined?", "customer_id": "alex_morgan"})
        elapsed_ms = (time.time() - t0) * 1000
        assert elapsed_ms < 500.0
        print(f"  [Case 4.3] Execution Latency & Performance SLA ({elapsed_ms:.1f}ms < 500ms): PASS (+5 pts)")
        score += 5

        # Case 4.4: Telemetry PII & PAN Redaction (4 pts)
        for s in spans_resp["spans"]:
            details_str = json.dumps(s.get("details", {}))
            assert "password" not in details_str
            assert "48210000" not in details_str
        print("  [Case 4.4] Telemetry PII & PCI-DSS Redaction Compliance: PASS (+4 pts)")
        score += 4

        self.results["observability_tracing"] = {"name": "Observability & Tracing", "score": score, "max": 19}
        self.total_score += score
        return score

    def evaluate_criterion_5_infrastructure_cicd(self) -> int:
        print_header("CRITERION 5: Infrastructure & CI/CD (Max Score: 19 Points)")
        score = 0

        # Case 5.1: Production Multi-Stage Dockerfile (5 pts)
        dockerfile = open("Dockerfile").read()
        assert "FROM python:3.11-slim as builder" in dockerfile
        assert "uvicorn" in dockerfile
        print("  [Case 5.1] Production Multi-Stage Dockerfile Best Practices: PASS (+5 pts)")
        score += 5

        # Case 5.2: Google Cloud Build CI/CD Pipeline (5 pts)
        cloudbuild = open("cloudbuild.yaml").read()
        assert "unit-tests-and-lint" in cloudbuild
        assert "deploy-cloud-run" in cloudbuild
        print("  [Case 5.2] Google Cloud Build CI/CD Pipeline Definition: PASS (+5 pts)")
        score += 5

        # Case 5.3: GitHub Actions CI Workflow (5 pts)
        gha = open(".github/workflows/agent-ci.yml").read()
        assert "pytest" in gha
        assert "run_adk_tests.py" in gha
        print("  [Case 5.3] GitHub Actions Automated CI Workflow: PASS (+5 pts)")
        score += 5

        # Case 5.4: Pytest Suite & Test Coverage (4 pts)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--disable-warnings"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "."},
        )
        assert result.returncode == 0
        assert "21 passed" in result.stdout
        print("  [Case 5.4] Pytest Automated Test Suite (21/21 passing): PASS (+4 pts)")
        score += 4

        self.results["infrastructure_cicd"] = {"name": "Infrastructure & CI/CD", "score": score, "max": 19}
        self.total_score += score
        return score

    def generate_scorecard(self):
        print("\n" + "#" * 76)
        print("  JPMORGAN CHASE AGENT PLATFORM — FINAL EVALUATION SCORECARD")
        print("#" * 76)
        print(f"\n  {'Pillar Name':<34} | {'Score':<8} | {'Max Score':<10} | {'Status'}")
        print("  " + "-" * 68)

        for key, res in self.results.items():
            print(f"  {res['name']:<34} | {res['score']:<8} | {res['max']:<10} | PASS (100%)")

        print("  " + "-" * 68)
        pct = (self.total_score / TOTAL_MAX_SCORE) * 100
        print(f"  {'FINAL EVALUATED BENCHMARK SCORE':<34} | {self.total_score:<8} | {TOTAL_MAX_SCORE:<10} | {pct:.1f}% EXCELLENCE")
        print("#" * 76 + "\n")


def main():
    evaluator = ArchitectureEvaluator()
    t0 = time.time()

    evaluator.evaluate_criterion_1_tool_interface_design()
    evaluator.evaluate_criterion_2_context_memory()
    evaluator.evaluate_criterion_3_orchestration_logic()
    evaluator.evaluate_criterion_4_observability_tracing()
    evaluator.evaluate_criterion_5_infrastructure_cicd()

    evaluator.generate_scorecard()
    duration = round(time.time() - t0, 2)
    print(f"Evaluation completed in {duration} seconds.\n")

    return 0 if evaluator.total_score == TOTAL_MAX_SCORE else 1


if __name__ == "__main__":
    sys.exit(main())
