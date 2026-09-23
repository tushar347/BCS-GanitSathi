"""Baseline B0: Reviewed Rule / Template Tutor.

Conforms to Section 8, Table 6 of GonitSathi Guideline:
- Fixed first-error hints and clarification rules.
- Deterministic keyword and pattern matching; no generative diagnosis.
- Represents the computational efficiency and non-LLM baseline floor.
"""

from __future__ import annotations

import re
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
from src.verifier.symbolic_verifier import ProblemReferenceDAG


class RuleTemplateTutor(BaseTutor):
    """B0 Baseline: Deterministic rule and template based tutor."""

    def __init__(self, name: str = "B0_RuleTemplate"):
        super().__init__(name=name)
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

        cleaned_text = raw_text.strip()

        # Rule 1: Empty or extremely vague input -> Ask clarification
        if len(cleaned_text) < 2 or re.match(r"^(কি|বুঝিনি|জানিনা|\?+|hello|hi)$", cleaned_text, re.IGNORECASE):
            latency = (time.perf_counter() - start_time) * 1000
            action = PedagogicalAction(
                action_type=ActionType.ASK_CLARIFICATION,
                payload="আপনার সমাধান বা ধাপটি স্পষ্টভাবে লিখুন।",
                is_protected_hint=True,
            )
            return BaselineStepResult(
                action=action,
                mathematical_status=MathematicalStatus.UNVERIFIABLE,
                latency_ms=latency,
                neural_calls=0,
                symbolic_calls=0,
                tokens_generated=len(action.payload.split()),
                raw_response=action.payload,
            )

        # Rule 2: Check against known error patterns defined in the DAG reference steps
        matched_error: Optional[str] = None
        for ref_step in problem_dag.reference_steps:
            for pat, err_label in ref_step.known_error_patterns.items():
                # Check for numerical or string match
                val = pat.split("=")[-1].strip() if "=" in pat else pat
                if val and val in cleaned_text:
                    matched_error = err_label
                    break
            if matched_error:
                break

        # Rule 3: Error detected
        is_first_err = False
        first_err_reason = None

        if matched_error:
            self.error_count += 1
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = matched_error

            # Rule template: graduated response based on error count
            if self.error_count == 1:
                action_type = ActionType.GIVE_CONCEPTUAL_HINT
                payload = "ধাপটি পুনরায় লক্ষ্য করুন। রাশিমালার সম্পর্ক বা গণনায় ভুল হতে পারে।"
            else:
                action_type = ActionType.OFFER_LOCAL_SCAFFOLD
                payload = f"সূত্রটি স্মরণ করুন: সমস্যার মূল চলকের সাথে প্রদত্ত মানগুলো সতর্কভাবে বসান ({problem_dag.reference_steps[0].description if problem_dag.reference_steps else ''})।"

            latency = (time.perf_counter() - start_time) * 1000
            action = PedagogicalAction(
                action_type=action_type,
                payload=payload,
                target_cause=CandidateCause.PERCENTAGE_BASE if "conceptual" in matched_error else CandidateCause.TRANSIENT_SLIP,
                is_protected_hint=True,
            )
            return BaselineStepResult(
                action=action,
                mathematical_status=MathematicalStatus.INVALID,
                is_first_error=is_first_err,
                first_error_reason=first_err_reason,
                predicted_cause=action.target_cause,
                latency_ms=latency,
                neural_calls=0,
                symbolic_calls=0,
                tokens_generated=len(payload.split()),
                raw_response=payload,
            )

        # Rule 4: Match correct answer or valid steps
        is_valid = False
        for ref_step in problem_dag.reference_steps:
            if ref_step.symbolic_expression and ref_step.symbolic_expression in cleaned_text:
                is_valid = True
                break
            # Check target variable
            val = ref_step.symbolic_expression.split("=")[-1].strip() if "=" in ref_step.symbolic_expression else ""
            if val and val in cleaned_text:
                is_valid = True
                break

        if is_valid or "উত্তর" in cleaned_text or "সঠিক" in cleaned_text:
            action = PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="আপনার এই ধাপটি সঠিক আছে। পরবর্তী ধাপে এগিয়ে যান।",
                target_cause=CandidateCause.NO_ERROR,
                is_protected_hint=True,
            )
            status = MathematicalStatus.VALID
            cause = CandidateCause.NO_ERROR
        else:
            # Fallback rule when unclassified
            action = PedagogicalAction(
                action_type=ActionType.REQUEST_INDEPENDENT_RETRY,
                payload="ধাপটি পুনরায় পরীক্ষা করে দেখুন এবং সঠিক সমীকরণটি লিখুন।",
                is_protected_hint=True,
            )
            status = MathematicalStatus.UNVERIFIABLE
            cause = CandidateCause.UNRESOLVED

        latency = (time.perf_counter() - start_time) * 1000
        return BaselineStepResult(
            action=action,
            mathematical_status=status,
            predicted_cause=cause,
            latency_ms=latency,
            neural_calls=0,
            symbolic_calls=0,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
        )
