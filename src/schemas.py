
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, constr, field_validator, model_validator

class Status(str, Enum):
    WORKING = "WORKING"
    NEED_PEER = "NEED_PEER"
    PROPOSED = "PROPOSED"
    READY_TO_SOLVE = "READY_TO_SOLVE"
    SOLVED = "SOLVED"

class FinalSolution(BaseModel):
    canonical_text: constr(strip_whitespace=True, min_length=1)
    sha256: Optional[constr(pattern=r"^[0-9a-f]{64}$")] = None

class Envelope(BaseModel):
    role: Optional[str] = None
    domain: Optional[str] = None
    tag: Optional[constr(pattern=r"^\[(CONTACT|SOLVED)\]$")] = None
    status: Status
    content: Optional[Dict[str, Any]] = None
    final_solution: Optional[FinalSolution] = None
    artifact: Optional[str] = None

    @model_validator(mode="after")
    def _solution_only_on_terminal(self):
        if self.status == Status.SOLVED and self.final_solution is None:
            raise ValueError("SOLVED requires final_solution.")
        if self.status != Status.SOLVED and self.final_solution is not None:
            raise ValueError("final_solution only allowed when SOLVED.")
        return self

    def is_solved(self) -> bool:
        return self.status == Status.SOLVED and self.final_solution is not None
