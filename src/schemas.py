from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

Status = Literal["WORKING", "ASKING", "SOLVED"]

class Solution(BaseModel):
    final_text: str = ""
    solution_signature: str = ""

class Envelope(BaseModel):
    agent: str = Field(..., description="Agent name, e.g., 'designer' or 'programmer'")
    status: Status
    public_message: str
    solution: Solution

    def is_solved(self) -> bool:
        pm = self.public_message or ""
        return self.status == "SOLVED" and "[SOLVED]" in pm
