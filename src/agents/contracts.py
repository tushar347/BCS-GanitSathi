from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.controller.schemas import ActionType, CandidateCause, MathematicalStatus


class AssessmentResult(BaseModel):
    interpreted_relation: str = ""
    evidence_spans: List[str] = Field(default_factory=list)
    interpretation_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    candidate_explanations: List[CandidateCause] = Field(default_factory=list)
    assistance_references: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    is_final_answer: bool = False
    reason_codes: List[str] = Field(default_factory=list)


class ProbeResponseAssessment(BaseModel):
    response_category: str
    evidence_spans: List[str] = Field(default_factory=list)
    interpretation_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_clarification: bool = False


class CurriculumDecision(BaseModel):
    action: str
    item_id: Optional[str] = None
    family_id: Optional[str] = None
    topic_group: Optional[str] = None
    subskill: Optional[str] = None
    difficulty: Optional[str] = None
    reason_code: str


class MotivationDecision(BaseModel):
    should_include: bool
    mode: str
    message: str = ""


class AgentTurnTrace(BaseModel):
    assessor_used_model: bool = False
    expert_used_model: bool = False
    curriculum_invoked: bool = False
    motivation_invoked: bool = True
    action_type: ActionType
    mathematical_status: MathematicalStatus
    probe_response_category: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    costs: Dict[str, int] = Field(default_factory=dict)


class ReflectionRecord(BaseModel):
    previous_uncertainty: float
    current_uncertainty: float
    uncertainty_change: float
    outcome: str
    next_action: str
    state_changed: bool


class AgenticCycleRecord(BaseModel):
    observe: Dict[str, object]
    reason: Dict[str, object]
    plan: Dict[str, object]
    act: Dict[str, object]
    reflect: ReflectionRecord
