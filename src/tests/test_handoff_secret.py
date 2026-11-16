import pytest

from lab8.db import connect
from lab8.handoff import HandoffError, make_handoff, sanitize
from lab8.runtime import ToolRejected, dispatch, run_react
from lab8.schemas import Budget
from lab8.tools import get_claim_view


def test_allowlist_drops_parent_secret_and_headers():
    payload = {
        "contract_version": "handoff.v1",
        "request_id": "REQ-1",
        "claim_id": "C-010",
        "principal_scope": "owner_order_only",
        "task": "check_applicable_policy",
        "facts": {"delay_days": 4, "carrier": "LOGIX_LOCAL"},
        "allowed_tools": ["lookup_policy"],
        "max_output_tokens": 400,
        "parent_secret": "CANARY_SECRET_PARENT_C010",
        "raw_headers": {"Authorization": "Bearer CANARY_SECRET_PARENT_C010"},
        "history": ["full chat"],
    }
    cleaned = sanitize(payload)
    assert "parent_secret" not in cleaned
    assert "CANARY_SECRET_" not in str(cleaned)
    assert set(cleaned) <= {
        "contract_version",
        "request_id",
        "claim_id",
        "principal_scope",
        "task",
        "facts",
        "allowed_tools",
        "max_output_tokens",
    }


def test_worker_cannot_receive_issue_refund():
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-2",
            claim_id="C-001",
            task="pay",
            facts={},
            allowed_tools=["issue_refund"],
        )


def test_claim_view_and_react_observation_omit_secret(public_db):
    conn = connect(public_db)
    view = get_claim_view(conn, "C-010")
    assert "CANARY_SECRET_" not in str(view)
    budget = Budget()

    def decide(obs):
        return {"final": {"status": "denied"}}

    outcome = run_react(conn, budget, observation={"claim": view}, decide=decide, max_steps=8, worker=True)
    with pytest.raises(ToolRejected):
        dispatch(conn, budget, "issue_refund", {"claim_id": "C-010"}, worker=True)
    conn.close()
    assert outcome["stopped"] == "final"
    assert "CANARY_SECRET_" not in str(outcome)


def test_worker_cannot_spoof_principal_to_read_another_order(public_db):
    conn = connect(public_db)

    def decide(_obs):
        return {
            "tool": "lookup_order",
            "args": {"order_id": "O-110", "principal_id": "P-200"},
        }

    outcome = run_react(
        conn,
        Budget(),
        observation={"claim": {"claim_id": "C-001"}},
        decide=decide,
        max_steps=1,
        worker=True,
    )
    conn.close()
    assert outcome["observation"]["last_result"]["visible"] is False
    assert outcome["observation"]["last_result"]["reason"] == "outside_principal_scope"


def test_worker_cannot_read_a_different_claim(public_db):
    conn = connect(public_db)

    def decide(_obs):
        return {"tool": "get_claim_view", "args": {"claim_id": "C-010"}}

    outcome = run_react(
        conn,
        Budget(),
        observation={"claim": {"claim_id": "C-001"}},
        decide=decide,
        max_steps=1,
        worker=True,
    )
    conn.close()
    assert outcome["observation"]["last_result"]["claim_id"] == "C-001"


def test_worker_cannot_forge_order_facts_for_a_quote(public_db):
    conn = connect(public_db)

    def decide(_obs):
        return {
            "tool": "compute_compensation",
            "args": {
                "order": {
                    "order_id": "O-107",
                    "status": "delivered",
                    "delay_days": 365,
                    "shipping_fee_vnd": 999999,
                    "paid_vnd": 999999999,
                    "damage_verified": True,
                    "carrier": "LOGIX_LOCAL",
                }
            },
        }

    outcome = run_react(
        conn,
        Budget(),
        observation={"claim": {"claim_id": "C-001"}},
        decide=decide,
        max_steps=1,
        worker=True,
    )
    conn.close()
    assert outcome["observation"]["last_result"]["amount_vnd"] == 35000


def test_agent_final_amount_cannot_replace_runtime_quote(public_db):
    conn = connect(public_db)
    step = {"n": 0}

    def decide(obs):
        step["n"] += 1
        if step["n"] == 1:
            return {"tool": "compute_compensation", "args": {"order": {"delay_days": 365}}}
        obs["last_result"]["amount_vnd"] = 999999
        return {"final": {"status": "ready", "proposal_amount": 999999}}

    outcome = run_react(
        conn,
        Budget(),
        observation={"claim": {"claim_id": "C-001"}},
        decide=decide,
        max_steps=2,
        worker=True,
    )
    conn.close()
    assert outcome["final"]["proposal_amount"] == 999999
    assert outcome["trusted_quote"]["amount_vnd"] == 35000


def test_single_trace_does_not_write_raw_ticket_when_order_missing(public_db):
    from lab8.shapes.single import run_claim

    conn = connect(public_db)
    conn.execute(
        "UPDATE claims SET order_id = NULL, ticket = ? WHERE claim_id = 'C-001'",
        ("customer text CANARY_SECRET_TICKET_LEAK",),
    )
    conn.commit()
    conn.close()

    result = run_claim("C-001", seed=11, store_path=str(public_db))
    trace_text = open(result.trace_path, encoding="utf-8").read()
    assert "CANARY_SECRET_TICKET_LEAK" not in trace_text
    assert '"last_tool": "get_claim_view"' in trace_text
