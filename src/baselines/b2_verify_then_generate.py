"""Baseline B2: Verify-Then-Generate Tutor.

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Uses the same restricted AST parser and SymPy symbolic verifier as GonitSathi.
- Pedagogical feedback is grounded directly in the verifier's mathematical status.
- Crucially: DOES NOT maintain a persistent Bayesian belief model, evidence admission governor,
  or multi-turn hypothesis commitment state.
- Demonstrates whether raw mathematical verification alone suffices without state governance.
"""

from __future__ import annotations

import time
from typing import List, Optional

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


class VerifyThenGenerateTutor(BaseTutor):
    """B2 Baseline: Step verifier grounded tutor without persistent diagnostic controller."""

    def __init__(
        self,
        name: str = "B2_VerifyThenGenerate",
        verifier: Optional[SymbolicVerifier] = None,
        normalizer: Optional[BengaliNormalizer] = None,
    ):
        super().__init__(name=name)
        self.normalizer = normalizer or BengaliNormalizer()
        self.verifier = verifier or SymbolicVerifier(normalizer=self.normalizer)
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.step_history: List[str] = []
        self.error_count: int = 0
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.step_history = []
        self.error_count = 0
        self.first_error_detected = False

    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        independent_group_id: Optional[str] = None,
    ) -> BaselineStepResult:
        start_time = time.perf_counter()
        self.step_history.append(raw_text)

        # 1. Normalize and extract expression
        expression = self.normalizer.extract_expression(
            raw_text,
            variable_aliases=problem_dag.variable_aliases,
        )

        # 2. Invoke SymPy verifier
        verification = self.verifier.verify_step(
            student_expression=expression,
            problem_dag=problem_dag,
        )

        is_first_err = False
        first_err_reason = None
        predicted_cause: Optional[CandidateCause] = None

        # 3. Formulate immediate pedagogical response based on verification result
        if verification.mathematical_status == MathematicalStatus.VALID:
            action = PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="আপনার গাণিতিক ধাপটি নির্ভুল হয়েছে। পরবর্তী ধাপে এগিয়ে যান।",
                target_cause=CandidateCause.NO_ERROR,
                is_protected_hint=True,
            )
            predicted_cause = CandidateCause.NO_ERROR

        elif verification.mathematical_status == MathematicalStatus.INVALID:
            self.error_count += 1
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = verification.verification_reason

            # Attribution derived strictly from single-turn verifier error catalog
            if "conceptual" in verification.verification_reason.lower():
                predicted_cause = CandidateCause.PERCENTAGE_BASE
            elif "arithmetic" in verification.verification_reason.lower() or "slip" in verification.verification_reason.lower():
                predicted_cause = CandidateCause.TRANSIENT_SLIP
            else:
                predicted_cause = CandidateCause.TRANSIENT_SLIP

            # Immediate unmitigated hint (no admission or delay)
            payload = f"গাণিতিক সম্পর্কে অমিল পাওয়া গেছে: {verification.verification_reason}। হিসাবটি পুনরায় যাচাই করুন।"
            action = PedagogicalAction(
                action_type=ActionType.GIVE_CONCEPTUAL_HINT,
                payload=payload,
                target_cause=predicted_cause,
                is_protected_hint=True,
            )

        else:
            # Unverifiable or syntax issue
            action = PedagogicalAction(
                action_type=ActionType.ASK_CLARIFICATION,
                payload="আপনার গাণিতিক রাশিটি স্পষ্টভাবে বোঝা যায়নি। সঠিক চলক বা সমীকরণ আকারে লিখুন।",
                is_protected_hint=True,
            )
            predicted_cause = CandidateCause.UNRESOLVED

        latency = (time.perf_counter() - start_time) * 1000

        # Note: B2 has NO persistent belief state or active commitments
        return BaselineStepResult(
            action=action,
            mathematical_status=verification.mathematical_status,
            beliefs={cause: 1.0 if cause == predicted_cause else 0.0 for cause in CandidateCause} if predicted_cause else {},
            active_commitments=[],  # B2 lacks persistent commitment governance
            predicted_cause=predicted_cause,
            is_first_error=is_first_err,
            first_error_reason=first_err_reason,
            latency_ms=latency,
            neural_calls=0,
            symbolic_calls=1,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
            metadata={
                "verification_reason": verification.verification_reason,
                "matched_reference_step_id": verification.matched_reference_step_id,
            },
        )
