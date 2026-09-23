"""Benchmark dataset loader and validator.

Conforms to Section 7.2, 7.3 of GonitSathi Guideline.
Validates GonitSathi-Bench JSON schemas to ensure problem families,
attempt histories, and diagnostic probes are correctly structured.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from src.controller.schemas import CandidateCause, DiagnosticProbe


class ReferenceStepSchema(BaseModel):
    step_id: str
    symbolic_expression: str
    alternative_forms: List[str] = Field(default_factory=list)
    known_error_patterns: Dict[str, str] = Field(default_factory=dict)


class AttemptHistorySchema(BaseModel):
    history_id: str
    history_type: str = Field(..., description="E.g., 'correct_work', 'conceptual_error', 'transient_slip', 'ambiguous'")
    events: List[Dict[str, str]] = Field(
        ..., 
        description="List of student events. Must include 'text', 'assistance_level', and 'independent_evidence_group'"
    )
    latent_cause: Optional[CandidateCause] = None


class ProblemFamilySchema(BaseModel):
    item_id: str
    family_id: str
    topic: str
    difficulty: str
    question_bn: str
    declared_variables: Dict[str, str]
    variable_aliases: Dict[str, List[str]] = Field(default_factory=dict)
    reference_steps: List[ReferenceStepSchema]
    probes: List[DiagnosticProbe] = Field(default_factory=list)
    attempt_histories: List[AttemptHistorySchema]


class BenchmarkDatasetSchema(BaseModel):
    split: str = Field(..., description="'train', 'dev', or 'test'")
    families: List[ProblemFamilySchema]


def load_and_validate_benchmark(dataset_dict: dict) -> BenchmarkDatasetSchema:
    """
    Validates a raw dictionary representing the benchmark dataset
    against the strict Pydantic schema.
    """
    return BenchmarkDatasetSchema(**dataset_dict)
