"""Base interface and return schemas for tutoring baselines (B0-B6, G).

Conforms to Section 8, Table 6, and Appendix C.1 of GonitSathi Guideline.
Provides a unified contract for single-step and episodic evaluation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.controller.schemas import (
    AssistanceLevel,
    CandidateCause,
    MathematicalStatus,
    PedagogicalAction,
)
from src.verifier.symbolic_verifier import ProblemReferenceDAG


@dataclass
class BaselineStepResult:
    """Unified result contract for each student interaction turn."""
    action: PedagogicalAction
    mathematical_status: MathematicalStatus = MathematicalStatus.UNVERIFIABLE
    beliefs: Dict[CandidateCause, float] = field(default_factory=dict)
    active_commitments: List[Dict[str, str]] = field(default_factory=list)
    predicted_cause: Optional[CandidateCause] = None
    is_first_error: bool = False
    first_error_reason: Optional[str] = None
    latency_ms: float = 0.0
    neural_calls: int = 0
    symbolic_calls: int = 0
    tokens_generated: int = 0
    raw_response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTutor(ABC):
    """Abstract base class for all comparison baselines (B0-B6) and GonitSathi (G)."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        """Reset internal state for a new student episode / history."""
        pass

    @abstractmethod
    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        independent_group_id: Optional[str] = None,
    ) -> BaselineStepResult:
        """Process an observed student step and return pedagogical action and diagnostic state."""
        pass
