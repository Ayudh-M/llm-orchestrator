from src.schemas import Envelope, Artifact, FinalSolution
from src.controller import run_controller

class Dummy:
    def __init__(self, answers):
        self.answers = answers
        self.i=0
    def step(self, task, transcript):
        env = self.answers[min(self.i, len(self.answers)-1)]
        self.i += 1
        return env, str(env)

def test_auto_promote():
    A = Dummy([{"role":"A","domain":"d","task_understanding":"","public_message":"", "artifact":{"type":"results","content":{}},"needs_from_peer":[],"handoff_to":"", "status":"PROPOSED","final_solution":{"canonical_text":"42"}}])
    B = Dummy([{"role":"B","domain":"d","task_understanding":"","public_message":"", "artifact":{"type":"results","content":{}},"needs_from_peer":[],"handoff_to":"", "status":"READY_TO_SOLVE","final_solution":{"canonical_text":"42"}}])
    res = run_controller("t", A, B, max_rounds=1)
    assert res["status"] == "CONSENSUS"
