"""Baseline B3: Bayesian Diagnostic Tutor.

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Small likelihood model with calibrated beliefs, templates, and probe bank access.
- Essential non-LLM control: Isolates whether an LLM is needed at all for diagnosis.
- Crucially: Unlike GonitSathi (G), B3 updates beliefs naively on every observation WITHOUT
  evidence admission governance (it does not enforce independent evidence group de-duplication,
  provenance checks, or bounded probing invariants).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from src.baselines.base import BaseTutor, BaselineStepResult
from src.controller.belief_updater import DEFAULT_PRIORS, LIKELIHOODS_UNASSISTED
from src.controller.schemas import (
    ActionType,
    AssistanceLevel,
    CandidateCause,
    MathematicalStatus,
    PedagogicalAction,
)
from src.normalizer.bengali_normalizer import BengaliNormalizer
from src.verifier.symbolic_verifier import ProblemReferenceDAG, SymbolicVerifier


class BayesianDiagnosticTutor(BaseTutor):
    """B3 Baseline: Pure Bayesian diagnostic updater without evidence governance."""

    def __init__(
        self,
        name: str = "B3_BayesianDiagnostic",
        activation_threshold: float = 0.80,
        verifier: Optional[SymbolicVerifier] = None,
        normalizer: Optional[BengaliNormalizer] = None,
    ):
        super().__init__(name=name)
        self.activation_threshold = activation_threshold
        self.normalizer = normalizer or BengaliNormalizer()
        self.verifier = verifier or SymbolicVerifier(normalizer=self.normalizer)
        self.beliefs: Dict[CandidateCause, float] = DEFAULT_PRIORS.copy()
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.step_history: List[str] = []
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.beliefs = DEFAULT_PRIORS.copy()
        self.step_history = []
        self.first_error_detected = False

    def _update_beliefs(
        self,
        math_status: MathematicalStatus,
        candidate_causes: List[CandidateCause],
    ) -> None:
        """Naive Bayesian likelihood update on every turn without admission filtering."""
        if math_status not in LIKELIHOODS_UNASSISTED:
            return

        likelihood_table = LIKELIHOODS_UNASSISTED[math_status]
        unnormalized = {}

        for cause in CandidateCause:
            prior = self.beliefs.get(cause, 0.1)
            lh = likelihood_table.get(cause, 0.1)
            if candidate_causes and cause in candidate_causes:
                lh *= 1.5
            unnormalized[cause] = prior * lh

        total = sum(unnormalized.values())
        if total > 0:
            self.beliefs = {c: val / total for c, val in unnormalized.items()}

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

        # 2. Symbolic verify
        verification = self.verifier.verify_step(
            student_expression=expression,
            problem_dag=problem_dag,
        )

        is_first_err = False
        first_err_reason = None
        candidate_causes: List[CandidateCause] = []

        if verification.mathematical_status == MathematicalStatus.VALID:
            candidate_causes = [CandidateCause.NO_ERROR]
        elif verification.mathematical_status == MathematicalStatus.INVALID:
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = verification.verification_reason

            if "conceptual" in verification.verification_reason.lower():
                candidate_causes = [CandidateCause.PERCENTAGE_BASE]
            else:
                candidate_causes = [CandidateCause.TRANSIENT_SLIP]

        # 3. Naive Bayesian belief update (NO evidence admission check, updates on every input)
        self._update_beliefs(verification.mathematical_status, candidate_causes)

        # 4. Top belief & commitment
        top_cause = max(self.beliefs.items(), key=lambda x: x[1])[0]
        top_prob = self.beliefs[top_cause]

        active_commitments = []
        if top_prob >= self.activation_threshold and top_cause != CandidateCause.NO_ERROR:
            active_commitments.append({
                "learner_id": self.learner_id or "unknown",
                "item_id": problem_dag.item_id,
                "cause": top_cause.value,
            })

        # 5. Pedagogical action selection via calibrated template rules
        if verification.mathematical_status == MathematicalStatus.VALID:
            action = PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="ধাপটি সঠিক। পরবর্তী ধাপে এগিয়ে যান।",
                target_cause=CandidateCause.NO_ERROR,
                is_protected_hint=True,
            )
        elif top_prob >= self.activation_threshold and top_cause == CandidateCause.PERCENTAGE_BASE:
            action = PedagogicalAction(
                action_type=ActionType.GIVE_CONCEPTUAL_HINT,
                payload="শতকরা বা মূল ভিত্তি নির্ণয়ে বিভ্রান্তি লক্ষ্য করা যাচ্ছে। ভিত্তি রাশিটি পুনরায় যাচাই করুন।",
                target_cause=top_cause,
                is_protected_hint=True,
            )
        elif top_prob >= self.activation_threshold and top_cause == CandidateCause.TRANSIENT_SLIP:
            action = PedagogicalAction(
                action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
                payload="গণনায় অসাবধানতাবশত ভুল হতে পারে। সমীকরণের যোগ-বিয়োগ পুনরায় গণনা করুন।",
                target_cause=top_cause,
                is_protected_hint=True,
            )
        else:
            action = PedagogicalAction(
                action_type=ActionType.REQUEST_INDEPENDENT_RETRY,
                payload="ধাপটি পুনরায় পরীক্ষা করে সমাধান করার চেষ্টা করুন।",
                target_cause=top_cause,
                is_protected_hint=True,
            )

        latency = (time.perf_counter() - start_time) * 1000

        return BaselineStepResult(
            action=action,
            mathematical_status=verification.mathematical_status,
            beliefs=dict(self.beliefs),
            active_commitments=active_commitments,
            predicted_cause=top_cause,
            is_first_error=is_first_err,
            first_error_reason=first_err_reason,
            latency_ms=latency,
            neural_calls=0,
            symbolic_calls=1,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
            metadata={"top_prob": round(top_prob, 4)},
        )
