"""Unit tests for Vertex AI Scale Memory Bank and Dreaming Compaction Service."""

import pytest
from jpmc_agent.memory.memory_bank import ScaleMemoryBank, memory_bank_store
from jpmc_agent.memory.dreaming_service import DreamingCompactionService


def test_memory_bank_seeding():
    memories = memory_bank_store.get_memories("alex_morgan")
    assert len(memories) >= 4
    channels = {m.channel for m in memories}
    assert "FRAUD_DETECTION" in channels
    assert "TELEPHONY_IVR" in channels
    assert "MOBILE_APP" in channels
    assert "TRAVEL_REGISTRY" in channels


def test_memory_bank_preload_context():
    preload = memory_bank_store.generate_preload_context("alex_morgan")
    assert "VERTEX AI MEMORY BANK PRELOAD" in preload
    assert "Chase Sapphire Preferred" in preload
    assert "SECURITY_LOCKED" in preload
    assert "The Savoy Hotel" in preload
    assert "Day 1 • 09:15 UTC" in preload


def test_memory_bank_search():
    results = memory_bank_store.search("alex_morgan", "Target")
    assert len(results) >= 1
    assert any("Target Store #1142" in r.summary for r in results)


def test_dreaming_compaction_service():
    memory_bank_store.seed_defaults()
    initial_count = len(memory_bank_store.get_memories("alex_morgan"))
    assert initial_count >= 4

    compaction = DreamingCompactionService.compact_customer_memories("alex_morgan")
    assert compaction["status"] == "COMPACTED"
    assert compaction["source_fragment_count"] == initial_count
    assert compaction["compacted_token_count"] < compaction["raw_token_count"]
    assert float(compaction["token_reduction_percentage"].replace("%", "")) > 50.0

    # Verify that stored memory now contains the compacted node
    updated_memories = memory_bank_store.get_memories("alex_morgan")
    assert len(updated_memories) == 1
    assert updated_memories[0].is_compacted_summary is True

    # Re-seed for further tests
    memory_bank_store.seed_defaults()
