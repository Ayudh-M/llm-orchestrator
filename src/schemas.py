
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, constr, validator

class Status(str, Enum):
    WORKING = "WORKING"
    NEED_PEER = "NEED_PEER"
    PROPOSED = "PROPOSED"
    READY_TO_SOLVE = "READY_TO_SOLVE"
    SOLVED = "SOLVED"

class FinalSolution(BaseModel):
    canonical_text: constr(strip_whitespace=True, min_length=1)
    sha256: Optional[constr(regex=r"^[0-9a-f]{64}$")] = None

class Envelope(BaseModel):
    role: Optional[str] = None
    domain: Optional[str] = None
    tag: Optional[constr(regex=r"^\[(CONTACT|SOLVED)\]$")] = None
    status: Status
    content: Optional[Dict[str, Any]] = None
    final_solution: Optional[FinalSolution] = None
    artifact: Optional[str] = None

    @validator("final_solution", always=True)
    def solution_only_on_terminal(cls, v, values):
        st = values.get("status")
        if st == Status.SOLVED and v is None:
            raise ValueError("SOLVED requires final_solution.")
        if st != Status.SOLVED and v is not None:
            raise ValueError("final_solution only allowed when SOLVED.")
        return v

    def is_solved(self) -> bool:
        return self.status == Status.SOLVED and self.final_solution is not None

