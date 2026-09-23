"""Baseline B4: Validated Learner-State Tutor (IntelliCode-inspired Adaptation).

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Centralized learner-state tracking with single-writer schema validation.
- Contextual BKT (Bayesian Knowledge Tracing) style probability updates for mastery/slip.
- Graduated hints (Level 1: conceptual prompt, Level 2: local scaffold, Level 3: worked step).
- Crucially: Unlike GonitSathi (G), B4 relies on single-writer state updates without
  bidirectional evidence retraction, independent evidence group gating, or active-claim contestation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
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


@dataclass
class BKTState:
    """Standard Bayesian Knowledge Tracing parameters for a skill."""
    p_mastery: float = 0.30
    p_transit: float = 0.15
    p_slip: float = 0.10
    p_guess: float = 0.20


class IntelliCodeTutor(BaseTutor):
    """B4 Baseline: Validated Central Learner-State Tutor (IntelliCode adaptation)."""

    def __init__(
        self,
        name: str = "B4_IntelliCode",
        verifier: Optional[SymbolicVerifier] = None,
        normalizer: Optional[BengaliNormalizer] = None,
    ):
        super().__init__(name=name)
        self.normalizer = normalizer or BengaliNormalizer()
        self.verifier = verifier or SymbolicVerifier(normalizer=self.normalizer)
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.bkt_state: BKTState = BKTState()
        self.step_history: List[str] = []
        self.error_count: int = 0
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.bkt_state = BKTState()
        self.step_history = []
        self.error_count = 0
        self.first_error_detected = False

    def _update_bkt(self, is_correct: bool) -> None:
        """Contextual BKT probability update."""
        p_m = self.bkt_state.p_mastery
        p_s = self.bkt_state.p_slip
        p_g = self.bkt_state.p_guess
        p_t = self.bkt_state.p_transit

        if is_correct:
            # P(L | Correct)
            num = p_m * (1 - p_s)
            denom = num + (1 - p_m) * p_g
        else:
            # P(L | Incorrect)
            num = p_m * p_s
            denom = num + (1 - p_m) * (1 - p_g)

        p_l_given_obs = num / denom if denom > 0 else p_m
        # Transition: P(L_next) = P(L_obs) + (1 - P(L_obs)) * P(Transit)
        self.bkt_state.p_mastery = p_l_given_obs + (1 - p_l_given_obs) * p_t

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

        # 2. Verify with SymPy
        verification = self.verifier.verify_step(
            student_expression=expression,
            problem_dag=problem_dag,
        )

        is_correct = (verification.mathematical_status == MathematicalStatus.VALID)
        self._update_bkt(is_correct)

        is_first_err = False
        first_err_reason = None
        predicted_cause: Optional[CandidateCause] = None

        if is_correct:
            predicted_cause = CandidateCause.NO_ERROR
            action = PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="আপনার গাণিতিক ধাপটি নির্ভুল। পরবর্তী পদক্ষেপে যান।",
                target_cause=CandidateCause.NO_ERROR,
                is_protected_hint=True,
            )
        else:
            self.error_count += 1
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = verification.verification_reason

            predicted_cause = CandidateCause.PERCENTAGE_BASE if "conceptual" in verification.verification_reason.lower() else CandidateCause.TRANSIENT_SLIP

            # Graduated hint policy based on error count
            if self.error_count == 1:
                action = PedagogicalAction(
                    action_type=ActionType.GIVE_CONCEPTUAL_HINT,
                    payload="ধাপটি পুনরায় লক্ষ্য করুন: মূল রাশিমালার সম্পর্কটি সঠিকভাবে প্রয়োগ হয়েছে কিনা যাচাই করুন।",
                    target_cause=predicted_cause,
                    is_protected_hint=True,
                )
            elif self.error_count == 2:
                action = PedagogicalAction(
                    action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
                    payload=f"স্থানীয় সূত্র নির্দেশিকা: {problem_dag.reference_steps[0].description if problem_dag.reference_steps else 'সমীকরণটি সাজান'}।",
                    target_cause=predicted_cause,
                    is_protected_hint=True,
                )
            else:
                action = PedagogicalAction(
                    action_type=ActionType.PROVIDE_WORKED_SOLUTION,
                    payload="সম্পূর্ণ নির্দেশনা: সমস্যাটির সমাধানের প্রমিত ধাপগুলো অনুধাবন করে পুনরায় চেষ্টা করুন।",
                    target_cause=predicted_cause,
                    is_protected_hint=False,
                )

        # BKT belief distribution over causes
        beliefs: Dict[CandidateCause, float] = {
            CandidateCause.NO_ERROR: round(self.bkt_state.p_mastery, 4),
            CandidateCause.PERCENTAGE_BASE: round((1 - self.bkt_state.p_mastery) * 0.5, 4),
            CandidateCause.TRANSIENT_SLIP: round((1 - self.bkt_state.p_mastery) * 0.3, 4),
            CandidateCause.LINGUISTIC_SLIP: round((1 - self.bkt_state.p_mastery) * 0.1, 4),
            CandidateCause.INTERFACE_SLIP: round((1 - self.bkt_state.p_mastery) * 0.05, 4),
            CandidateCause.UNRESOLVED: round((1 - self.bkt_state.p_mastery) * 0.05, 4),
        }

        # Central state commitment: commits whenever mastery is below 0.20
        active_commitments = []
        if self.bkt_state.p_mastery < 0.20 and predicted_cause != CandidateCause.NO_ERROR:
            active_commitments.append({
                "learner_id": self.learner_id or "unknown",
                "item_id": problem_dag.item_id,
                "cause": predicted_cause.value if predicted_cause else "conceptual_error",
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
            metadata={"p_mastery": round(self.bkt_state.p_mastery, 4), "error_count": self.error_count},
        )
