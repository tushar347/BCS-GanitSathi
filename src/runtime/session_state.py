from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.controller.schemas import AssistanceLevel, DiagnosticProbe


class SessionTurn(BaseModel):
    turn_index: int
    student_text: str
    released_text: str
    item_id: str
    action_type: str
    mathematical_status: str
    beliefs: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TutoringSessionState(BaseModel):
    learner_id: str
    item_id: str
    family_id: str
    turn_index: int = 0
    consecutive_errors: int = 0
    consecutive_successes: int = 0
    seen_families: List[str] = Field(default_factory=list)
    pending_probe: Optional[DiagnosticProbe] = None
    pending_probe_item_id: Optional[str] = None
    last_assistance_level: AssistanceLevel = AssistanceLevel.NONE
    turns: List[SessionTurn] = Field(default_factory=list)
