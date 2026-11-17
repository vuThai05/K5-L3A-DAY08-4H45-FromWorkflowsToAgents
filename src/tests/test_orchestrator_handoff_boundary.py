"""Exercise the investigator boundary through the orchestrator."""

import json
from pathlib import Path

from lab8.handoff import READONLY_TOOLS
from lab8.shapes import orchestrator


def test_orchestrator_handoff_contains_only_read_tools(public_db, monkeypatch):
    original = orchestrator.run_readonly_investigators
    handoffs = []

    def observe(conn, budget, handoff, principal_id):
        handoffs.append(handoff)
        return original(conn, budget, handoff, principal_id)

    monkeypatch.setattr(orchestrator, "run_readonly_investigators", observe)
    result = orchestrator.run_claim("C-001", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    assert len(handoffs) == 1
    handoff = handoffs[0]
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert {"lookup_order", "compute_compensation"} <= set(handoff["allowed_tools"])
    assert handoff["facts"] == {}
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert not any(secret in json.dumps(trace) for secret in ("CANARY_SECRET_", "raw_headers", "ticket"))
