"""Baseline B5: Plan and Assessment Memory (ScaffoldLM-inspired Adaptation).

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Explicit stepwise scaffold plan with an Assess-Act-Track-Record memory loop.
- Tracks step progress index (k of N reference steps).
- Assesses student mastery per step and selects pedagogical actions based on current step status.
- Crucially: Relies on step-completion memory without GonitSathi's evidence admission governance,
  calibrated entropy gating, or bounded diagnostic probing invariants.
"""

from __future__ import annotations

import time
from typing import Dict, Optional

from src.baselines.base import BaseTutor, BaselineStepResult
from src.controller.schemas import (
    ActionType,
    AssistanceLevel,
    CandidateCause,
    MathematicalStatus,
    PedagogicalAction,
)
from src.normalizer.bengali_normalizer import BengaliNormalizer
from src.verifier.symbolic_verifier import ProblemReferenceDAG, SymbolicVerifier


class ScaffoldLMTutor(BaseTutor):
    """B5 Baseline: Step plan, progress, and assessment memory tutor (ScaffoldLM adaptation)."""

    def __init__(
        self,
        name: str = "B5_ScaffoldLM",
        verifier: Optional[SymbolicVerifier] = None,
        normalizer: Optional[BengaliNormalizer] = None,
    ):
        super().__init__(name=name)
        self.normalizer = normalizer or BengaliNormalizer()
        self.verifier = verifier or SymbolicVerifier(normalizer=self.normalizer)
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.current_step_index: int = 0
        self.step_assessment_memory: Dict[int, str] = {}
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.current_step_index = 0
        self.step_assessment_memory = {}
        self.first_error_detected = False

    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        independent_group_id: Optional[str] = None,
    ) -> BaselineStepResult:
        start_time = time.perf_counter()

        expression = self.normalizer.extract_expression(
            raw_text,
            variable_aliases=problem_dag.variable_aliases,
        )

        verification = self.verifier.verify_step(
            student_expression=expression,
            problem_dag=problem_dag,
        )

        is_first_err = False
        first_err_reason = None
        predicted_cause: Optional[CandidateCause] = None

        total_steps = len(problem_dag.reference_steps) if problem_dag.reference_steps else 1

        # 1. Assess & Track Memory Loop
        if verification.mathematical_status == MathematicalStatus.VALID:
            self.step_assessment_memory[self.current_step_index] = "mastered"
            predicted_cause = CandidateCause.NO_ERROR
            if self.current_step_index < total_steps - 1:
                self.current_step_index += 1
                action = PedagogicalAction(
                    action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                    payload=f"ধাপ {self.current_step_index} সম্পন্ন হয়েছে। এবার পরবর্তী ধাপ {self.current_step_index + 1}-এ অগ্রসর হোন।",
                    target_cause=CandidateCause.NO_ERROR,
                    is_protected_hint=True,
                )
            else:
                action = PedagogicalAction(
                    action_type=ActionType.OFFER_TRANSFER_QUESTION,
                    payload="সম্পূর্ণ সমাধান নির্ভুল হয়েছে! আপনি কি এই নিয়মের আরেকটি অনুশীলনী প্রশ্ন সমাধান করতে চান?",
                    target_cause=CandidateCause.NO_ERROR,
                    is_protected_hint=False,
                )
        else:
            self.step_assessment_memory[self.current_step_index] = "needs_remediation"
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = verification.verification_reason

            predicted_cause = CandidateCause.PERCENTAGE_BASE if "conceptual" in verification.verification_reason.lower() else CandidateCause.TRANSIENT_SLIP

            # Plan-based scaffold: direct student back to the current step goal
            curr_ref = (
                problem_dag.reference_steps[self.current_step_index].description
                if self.current_step_index < len(problem_dag.reference_steps)
                else "সমস্যার ধাপটি"
            )
            action = PedagogicalAction(
                action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
                payload=f"পরিকল্পনার ধাপ {self.current_step_index + 1} সম্পন্ন করতে লক্ষ্য রাখুন: {curr_ref}।",
                target_cause=predicted_cause,
                is_protected_hint=True,
            )

        # Plan-progress belief distribution
        progress_ratio = (self.current_step_index + (1 if is_first_err is False else 0)) / max(1, total_steps)
        beliefs = {
            CandidateCause.NO_ERROR: round(progress_ratio, 4),
            CandidateCause.PERCENTAGE_BASE: round((1 - progress_ratio) * 0.5, 4),
            CandidateCause.TRANSIENT_SLIP: round((1 - progress_ratio) * 0.3, 4),
            CandidateCause.LINGUISTIC_SLIP: round((1 - progress_ratio) * 0.1, 4),
            CandidateCause.INTERFACE_SLIP: round((1 - progress_ratio) * 0.05, 4),
            CandidateCause.UNRESOLVED: round((1 - progress_ratio) * 0.05, 4),
        }

        # Active commitments when progress is stalled
        active_commitments = []
        if self.step_assessment_memory.get(self.current_step_index) == "needs_remediation":
            active_commitments.append({
                "learner_id": self.learner_id or "unknown",
                "item_id": problem_dag.item_id,
                "cause": predicted_cause.value if predicted_cause else "remediation_needed",
            })

        latency = (time.perf_counter() - start_time) * 1000

        return BaselineStepResult(
            action=action,
            mathematical_status=verification.mathematical_status,
            beliefs=beliefs,
            active_commitments=active_commitments,
            predicted_cause=predicted_cause,
            is_first_error=is_first_err,
            first_error_reason=first_err_reason,
            latency_ms=latency,
            neural_calls=0,
            symbolic_calls=1,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
            metadata={"current_step_index": self.current_step_index, "plan_progress": round(progress_ratio, 2)},
        )
