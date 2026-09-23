"""Wrapper for GonitSathi controller to conform to BaseTutor interface."""

from __future__ import annotations

import time
from typing import Optional

from src.baselines.base import BaseTutor, BaselineStepResult
from src.controller.diagnostic_controller import DiagnosticController
from src.controller.schemas import (
    AssistanceLevel,
    ClaimStatus,
)
from src.verifier.symbolic_verifier import ProblemReferenceDAG


class GonitSathiTutor(BaseTutor):
    """GonitSathi full system (G) conforming to BaseTutor."""

    def __init__(
        self,
        name: str = "GonitSathi_G",
        activation_threshold: float = 0.80,
        retention_threshold: float = 0.40,
        entropy_threshold: float = 0.40,
    ):
        super().__init__(name=name)
        self.activation_threshold = activation_threshold
        self.retention_threshold = retention_threshold
        self.entropy_threshold = entropy_threshold
        self.controller: Optional[DiagnosticController] = None
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.controller = DiagnosticController(
            activation_threshold=self.activation_threshold,
            retention_threshold=self.retention_threshold,
            entropy_threshold=self.entropy_threshold,
        )

    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        independent_group_id: Optional[str] = None,
    ) -> BaselineStepResult:
        start_time = time.perf_counter()
        if self.controller is None:
            self.reset("default_learner", problem_dag)

        group_id = independent_group_id or "default_group"
        action, audit, obs = self.controller.process_student_step(
            raw_text=raw_text,
            problem_dag=problem_dag,
            learner_id=self.learner_id or "default_learner",
            independent_group_id=group_id,
            assistance_level=assistance_level,
        )

        top_cause, _ = self.controller.belief_updater.get_top_candidate()
        beliefs = dict(self.controller.belief_updater.beliefs)

        active_commitments = []
        for cause, hyp in self.controller.belief_updater.active_hypotheses.items():
            if hyp.status == ClaimStatus.ACTIVE:
                active_commitments.append({
                    "learner_id": self.learner_id or "default_learner",
                    "item_id": problem_dag.item_id,
                    "cause": cause.value,
                })

        latency = (time.perf_counter() - start_time) * 1000

        return BaselineStepResult(
            action=action,
            mathematical_status=obs.mathematical_status,
            beliefs=beliefs,
            active_commitments=active_commitments,
            predicted_cause=top_cause,
            latency_ms=latency,
            neural_calls=0,
            symbolic_calls=1,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
        )
