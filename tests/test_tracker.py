"""Smoke tests for Chainsight Forensics."""
import os
os.environ.setdefault("MIMO_API_KEY", "test-key")
os.environ.setdefault("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")
os.environ.setdefault("ETH_RPC", "https://eth.llamarpc.com")

import pytest
from src.tracker import TokenTracker


def test_tracker_basic():
    t = TokenTracker()
    t.record("hop_walker", prompt=100, completion=50)
    snap = t.snapshot()
    assert snap["hop_walker"]["total_tokens"] == 150


def test_tracker_seven_agents():
    t = TokenTracker()
    for a in ["address_tagger", "hop_walker", "bridge_decoder", "mixer_detector",
              "swap_decoder", "exchange_resolver", "synthesis_reasoner"]:
        t.record(a, prompt=200, completion=100)
    snap = t.snapshot()
    assert len(snap) == 7


def test_main_module():
    from src import main
    assert main.app is not None


def test_engine_module():
    from src import engine
    assert engine is not None


def test_agents_module():
    from src import agents
    if hasattr(agents, "AGENT_DESCRIPTORS"):
        assert len(agents.AGENT_DESCRIPTORS) >= 7
