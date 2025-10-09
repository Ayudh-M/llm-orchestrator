from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any, Optional

Status = Literal["WORKING", "NEED_PEER", "PROPOSED", "READY_TO_SOLVE", "SOLVED"]
Tag = Literal["[CONTACT]","[SOLVED]"]

class Artifact(BaseModel):
    type: Literal["component_spec","code_patch","outline","fact_pack","source_pack","plan","dataset","results"]
    content: Dict[str, Any] = Field(default_factory=dict)

class FinalSolution(BaseModel):
    canonical_text: str = ""
    sha256: str = ""

class Request(BaseModel):
    to_peer: Optional[str] = None

class Meta(BaseModel):
    strategy_id: Optional[str] = None
    roleset_id: Optional[str] = None
    decoding: Dict[str, Any] = Field(default_factory=dict)
    guardrails: Dict[str, Any] = Field(default_factory=dict)

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
    # New protocol fields (backward-compatible)
    tags: List[Tag] = Field(default_factory=list)
    request: Request = Field(default_factory=Request)
    meta: Meta = Field(default_factory=Meta)

    def is_solved(self) -> bool:
        pm = self.public_message or ""
        has_tag = ("[SOLVED]" in pm) or ("[SOLVED]" in self.tags)
        return self.status == "SOLVED" and has_tag and bool((self.final_solution or FinalSolution()).canonical_text)
