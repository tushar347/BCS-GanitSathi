"""Data schemas for GonitSathi controller, verifier, and observer.

Conforms to Appendix A.1 and Sections 2.3, 5.1 of GonitSathi Guideline.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CandidateCause(str, Enum):
    CONCEPTUAL_ERROR = "conceptual_error"
    PERCENTAGE_BASE = "percentage_base"
    TRANSIENT_SLIP = "transient_slip"
    LINGUISTIC_SLIP = "linguistic_slip"
    INTERFACE_SLIP = "interface_slip"
    NO_ERROR = "no_error"
    UNRESOLVED = "unresolved"


class AssistanceLevel(str, Enum):
    NONE = "none"
    CONCEPTUAL_HINT = "conceptual_hint"
    KEY_EQUATION_SUPPLIED = "key_equation_supplied"
    WORKED_SOLUTION = "worked_solution"


class MathematicalStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    UNVERIFIABLE = "unverifiable"
    UNSUPPORTED = "unsupported"


class InterpretationStatus(str, Enum):
    SUPPORTED = "supported"
    UNRESOLVED = "unresolved"


class ClaimStatus(str, Enum):
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    CONTESTED = "contested"
    RETRACTED = "retracted"


class ActionType(str, Enum):
    ASK_CLARIFICATION = "ask_clarification"
    ASK_DIAGNOSTIC_PROBE = "ask_diagnostic_probe"
    ACKNOWLEDGE_CORRECT_STEP = "acknowledge_correct_step"
    GIVE_CONCEPTUAL_HINT = "give_conceptual_hint"
    OFFER_LOCAL_SCAFFOLD = "offer_local_scaffold"
    REQUEST_INDEPENDENT_RETRY = "request_independent_retry"
    OFFER_TRANSFER_QUESTION = "offer_transfer_question"
    PROVIDE_WORKED_SOLUTION = "provide_worked_solution"
    DEFER_UNSUPPORTED = "defer_unsupported"


class StudentIntent(str, Enum):
    ATTEMPT = "attempt"
    CLARIFICATION_QUESTION = "clarification_question"
    REQUEST_HINT = "request_hint"
    REQUEST_SOLUTION = "request_solution"
    REQUEST_EXPLANATION = "request_explanation"
    CONFIRMATION = "confirmation"
    SKIP = "skip"
    META = "meta"
    UNKNOWN = "unknown"


class VerificationResult(BaseModel):
    mathematical_status: MathematicalStatus
    interpretation_status: InterpretationStatus
    verification_reason: str
    normalized_expression: Optional[str] = None
    matched_reference_step_id: Optional[str] = None
    is_alternative_strategy: bool = False


class Observation(BaseModel):
    event_id: str
    learner_id: str
    item_id: str
    family_id: str
    independent_evidence_group: str
    event_type: str = "student_step"
    original_text: str
    normalized_text: str
    assistance_level: AssistanceLevel = AssistanceLevel.NONE
    source_type: str = "independent_practice"
    interpretation_status: InterpretationStatus = InterpretationStatus.SUPPORTED
    interpretation_uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    mathematical_status: MathematicalStatus
    verification_reason: str = ""
    candidate_causes: List[CandidateCause] = Field(default_factory=list)
    evidence_admitted: bool = True
    claim_status: ClaimStatus = ClaimStatus.PROVISIONAL
    controller_version: str = "v0.2.0-rc"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HypothesisRecord(BaseModel):
    hypothesis_id: str
    learner_id: str
    skill: str
    error_code: CandidateCause
    context: str = ""
    supporting_event_ids: List[str] = Field(default_factory=list)
    contradicting_event_ids: List[str] = Field(default_factory=list)
    assistance_status: AssistanceLevel = AssistanceLevel.NONE
    probability: float = 0.5
    status: ClaimStatus = ClaimStatus.PROVISIONAL
    creation_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latest_update: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    controller_version: str = "v0.2.0-rc"


class DiagnosticProbe(BaseModel):
    probe_id: str
    target_ambiguity: str
    prompt_bn: str
    prompt_en: str
    candidate_causes: List[CandidateCause]
    # Response categories -> likelihood mapping P(ResponseCategory | Cause)
    response_model: Dict[str, Dict[CandidateCause, float]]
    expected_burden_seconds: float = 15.0


class PedagogicalAction(BaseModel):
    action_type: ActionType
    payload: str
    target_cause: Optional[CandidateCause] = None
    cited_fact_ids: List[str] = Field(default_factory=list)
    probe: Optional[DiagnosticProbe] = None
    is_protected_hint: bool = True


# Backward-compatibility aliases for controller modules
ObservationRecord = Observation
LearnerClaim = HypothesisRecord
InstructionalAction = PedagogicalAction
