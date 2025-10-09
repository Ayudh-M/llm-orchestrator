from src.controller import run_controller
from src.agents_mock import MockAgent

def test_mock_consensus_two_rounds():
    A = MockAgent(name="A", role="Writer", domain="t", peer_role="Checker")
    B = MockAgent(name="B", role="Checker", domain="t", peer_role="Writer")
    out = run_controller("any task", A, B, max_rounds=4)
    assert out["status"] in ("CONSENSUS","NO_CONSENSUS")
    # With our simple two-turn dance they should converge
    assert out["status"] == "CONSENSUS"
    assert out["rounds"] <= 3
