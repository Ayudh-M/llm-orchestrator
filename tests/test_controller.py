
from src.controller import run_controller
from src.agents_mock import RuleBasedMock, EchoPeerMock

def test_consensus_on_equal_answers():
    A = RuleBasedMock("42")
    B = EchoPeerMock("fallback")
    res = run_controller("task", A, B, max_rounds=3)
    assert res["status"] == "CONSENSUS"
    assert res["canonical_text"] == "42"

def test_no_consensus_when_different():
    class OtherMock(RuleBasedMock):
        def __init__(self): super().__init__("x")
        def step(self, task, transcript):
            return {"status":"SOLVED","tag":"[SOLVED]","final_solution":{"canonical_text":"x"}}, "x"
    A = RuleBasedMock("a")
    B = OtherMock()
    res = run_controller("task", A, B, max_rounds=1)
    assert res["status"] == "NO_CONSENSUS"
