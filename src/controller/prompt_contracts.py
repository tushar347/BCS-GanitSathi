"""Prompt and schema contracts for Extractor and Realizer LLMs.

Conforms to Appendix B.1 and B.2 of GonitSathi Guideline:
- Forbids LLMs from writing directly to learner state.
- Ensures mathematical verification comes from the verifier, not extractor claims.
- Constrains Realizer to authorized actions and facts in Bengali.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from src.controller.schemas import CandidateCause, ActionType


class ExtractorOutputContract(BaseModel):
    """Output contract for LLM evidence parsing (Appendix B.1)."""
    interpreted_relation: str = Field(
        ...,
        description="Extracted mathematical equation or relation string, e.g. 'new_quantity = 100 - 25'"
    )
    evidence_spans: List[str] = Field(
        default_factory=list,
        description="Exact substrings from the student input that ground this interpretation"
    )
    interpretation_uncertainty: float = Field(
        ..., ge=0.0, le=1.0,
        description="Interpretation uncertainty (0.0=clear, 1.0=highly ambiguous)"
    )
    candidate_explanations: List[CandidateCause] = Field(
        default_factory=list,
        description="Candidate error hypotheses suggested by student input"
    )
    assistance_references: List[str] = Field(
        default_factory=list,
        description="Any hints or equations from recent tutor turns that student may have relied on"
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if input is ambiguous or underspecified"
    )


class RealizerInputContract(BaseModel):
    """Input payload provided to LLM Realizer (Appendix B.2)."""
    action_type: ActionType
    target_cause: Optional[CandidateCause] = None
    permitted_facts: List[str] = Field(default_factory=list)
    recent_dialogue_context: List[str] = Field(default_factory=list)
    allowed_disclosure_level: str = "protected_hint"  # or "authorized_worked_example"


class RealizerOutputContract(BaseModel):
    """Output contract for LLM response generation (Appendix B.2)."""
    bengali_response_text: str = Field(
        ...,
        description="Generated tutor response in polite, clear Bengali"
    )
    cited_fact_ids: List[str] = Field(
        default_factory=list,
        description="IDs of permitted facts actually referenced"
    )
    questions_asked_count: int = Field(
        ..., ge=0, le=1,
        description="Number of questions asked (must be <= 1)"
    )
    fallback_signal_triggered: bool = Field(
        default=False,
        description="True if LLM determined facts were insufficient to formulate response"
    )
