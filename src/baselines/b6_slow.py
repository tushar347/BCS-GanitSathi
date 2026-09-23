"""Baseline B6: Diagnostic Reasoning Workspace (SLOW-inspired Adaptation).

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Explicit diagnostic reasoning workspace separating internal diagnosis from tutor actions.
- Internal counterfactual simulation: before committing to a diagnosis, simulates an internal check
  (e.g., whether an arithmetic slip could account for the observed error instead of a deep conceptual flaw).
- Crucially: Unlike GonitSathi (G) which selectively asks ONE real diagnostic probe to the human learner
  under a bounded-probing invariant, B6 uses extra internal model simulation turns.
- Tests whether internal counterfactual computation can substitute for interactive student evidence.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

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


class SlowWorkspaceTutor(BaseTutor):
    """B6 Baseline: Diagnostic Reasoning Workspace with counterfactual simulation (SLOW adaptation)."""

    def __init__(
        self,
        name: str = "B6_SLOW",
        verifier: Optional[SymbolicVerifier] = None,
        normalizer: Optional[BengaliNormalizer] = None,
    ):
        super().__init__(name=name)
        self.normalizer = normalizer or BengaliNormalizer()
        self.verifier = verifier or SymbolicVerifier(normalizer=self.normalizer)
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.diagnostic_workspace: List[Dict[str, str]] = []
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.diagnostic_workspace = []
        self.first_error_detected = False

    def _internal_counterfactual_simulation(
        self,
        student_expression: str,
        problem_dag: ProblemReferenceDAG,
        preliminary_cause: CandidateCause,
    ) -> CandidateCause:
        """Internal reasoning workspace simulating counterfactual hypotheses."""
        # Check if the error could be explained by a simple off-by-one or arithmetic slip
        # rather than a structural misconception
        if preliminary_cause == CandidateCause.PERCENTAGE_BASE:
            # Workspace counterfactual: test if expression differs from target only by a small integer delta
            for step in problem_dag.reference_steps:
                target_val_str = step.symbolic_expression.split("=")[-1].strip() if "=" in step.symbolic_expression else ""
                student_val_str = student_expression.split("=")[-1].strip() if "=" in student_expression else student_expression
                try:
                    target_num = float(target_val_str)
                    student_num = float(student_val_str)
                    if abs(target_num - student_num) <= 1.0:
                        # Counterfactual holds: off-by-one slip is plausible
                        return CandidateCause.TRANSIENT_SLIP
                except ValueError:
                    pass
        return preliminary_cause

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
        simulated_cause: Optional[CandidateCause] = None

        if verification.mathematical_status == MathematicalStatus.VALID:
            simulated_cause = CandidateCause.NO_ERROR
            action = PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="আপনার সমাধান সঠিক রয়েছে। পরবর্তী ধাপে এগিয়ে যান।",
                target_cause=CandidateCause.NO_ERROR,
                is_protected_hint=True,
            )
        else:
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = verification.verification_reason

            preliminary = (
                CandidateCause.PERCENTAGE_BASE
                if "conceptual" in verification.verification_reason.lower()
                else CandidateCause.TRANSIENT_SLIP
            )

            # B6 Workspace: Run internal counterfactual reasoning loop
            simulated_cause = self._internal_counterfactual_simulation(
                student_expression=expression,
                problem_dag=problem_dag,
                preliminary_cause=preliminary,
            )

            self.diagnostic_workspace.append({
                "step": raw_text,
                "preliminary": preliminary.value,
                "simulated_adjudication": simulated_cause.value,
            })

            # Action formulated after counterfactual check
            if simulated_cause == CandidateCause.TRANSIENT_SLIP:
                action = PedagogicalAction(
                    action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
                    payload="হিসাবের মধ্যে সামান্য অসঙ্গতি দেখা যাচ্ছে। যোগ-বিয়োগের গণনাটি পুনরায় পরীক্ষা করুন।",
                    target_cause=simulated_cause,
                    is_protected_hint=True,
                )
            else:
                action = PedagogicalAction(
                    action_type=ActionType.GIVE_CONCEPTUAL_HINT,
                    payload="সমস্যার গাণিতিক সম্পর্কের মূল ধারণাটি পুনরায় বিবেচনা করুন।",
                    target_cause=simulated_cause,
                    is_protected_hint=True,
                )

        # Beliefs after internal workspace simulation
        beliefs: Dict[CandidateCause, float] = {
            CandidateCause.NO_ERROR: 0.90 if simulated_cause == CandidateCause.NO_ERROR else 0.05,
            CandidateCause.PERCENTAGE_BASE: 0.70 if simulated_cause == CandidateCause.PERCENTAGE_BASE else 0.15,
            CandidateCause.TRANSIENT_SLIP: 0.70 if simulated_cause == CandidateCause.TRANSIENT_SLIP else 0.15,
            CandidateCause.LINGUISTIC_SLIP: 0.05,
            CandidateCause.INTERFACE_SLIP: 0.02,
            CandidateCause.UNRESOLVED: 0.03,
        }
        # Normalize
        b_sum = sum(beliefs.values())
        beliefs = {k: round(v / b_sum, 4) for k, v in beliefs.items()}

        active_commitments = []
        if simulated_cause != CandidateCause.NO_ERROR:
            active_commitments.append({
                "learner_id": self.learner_id or "unknown",
                "item_id": problem_dag.item_id,
                "cause": simulated_cause.value,
            })

        latency = (time.perf_counter() - start_time) * 1000

        return BaselineStepResult(
            action=action,
            mathematical_status=verification.mathematical_status,
            beliefs=beliefs,
            active_commitments=active_commitments,
            predicted_cause=simulated_cause,
            is_first_error=is_first_err,
            first_error_reason=first_err_reason,
            latency_ms=latency,
            neural_calls=1,  # B6 accounts for an internal simulated reasoning call
            symbolic_calls=2,  # Verification + counterfactual delta check
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
            metadata={"workspace_entries": len(self.diagnostic_workspace)},
        )
