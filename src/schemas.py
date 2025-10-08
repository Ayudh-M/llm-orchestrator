from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

Status = Literal["WORKING", "NEED_PEER", "PROPOSED", "READY_TO_SOLVE", "SOLVED"]

class Artifact(BaseModel):
    type: Literal["component_spec","code_patch","outline","fact_pack","source_pack","plan","dataset","results"]
    content: Dict[str, Any] = Field(default_factory=dict)

class FinalSolution(BaseModel):
    canonical_text: str = ""

class Envelope(BaseModel):
    role: str
    domain: str
    task_understanding: str
    public_message: str
    artifact: Artifact
    needs_from_peer: List[str] = Field(default_factory=list)
    handoff_to: str
    status: Status
    final_solution: FinalSolution

    def is_solved(self) -> bool:
        pm = self.public_message or ""
        return self.status == "SOLVED" and "[SOLVED]" in pm and bool(self.final_solution.canonical_text)
