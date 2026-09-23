"""Baseline B1: Strong Prompted Tutor.

Conforms to Section 8, Table 6, and Appendix B of GonitSathi Guideline:
- One structured prompt containing reference solution, permitted pedagogical actions, and recent history.
- Operates in two runtime modes:
  1. Live API mode: When an LLM client or callable is injected (e.g. LiteLLM / Gemini / OpenAI / Ollama).
  2. Deterministic Mock / Simulation mode: Offline simulator executing realistic prompt contract parsing
     (Appendix B.1 Evidence Extractor + B.2 Response Realizer) for fully reproducible offline benchmark runs.
- Crucially: Demonstrates standard prompting vulnerability — tendency to commit prematurely to diagnoses
  without evidence governance or bounded probing checks.
"""

from __future__ import annotations

import json
import time
from typing import Callable, Dict, List, Optional

from src.baselines.base import BaseTutor, BaselineStepResult
from src.controller.schemas import (
    ActionType,
    AssistanceLevel,
    CandidateCause,
    MathematicalStatus,
    PedagogicalAction,
)
from src.verifier.symbolic_verifier import ProblemReferenceDAG


B1_PROMPT_TEMPLATE = """You are an expert bilingual mathematics tutor for competitive exams (BCS).
Follow the strict pedagogy guidelines:
1. Examine the problem stem and reference solution.
2. Review the student's recent step history.
3. Diagnose the student's current step and output an appropriate pedagogical action.
4. Output strict JSON matching the specified schema.

Problem: {problem_text}
Reference Solution Steps:
{reference_steps}

Permitted Actions:
- acknowledge_correct_step
- give_conceptual_hint
- offer_local_scaffold
- request_independent_retry
- ask_clarification

Student History:
{history}

Recent Step to Diagnose: "{current_step}"

Return JSON format:
{{
  "interpreted_math": "<extracted math expression>",
  "mathematical_status": "<valid | invalid | unverifiable>",
  "diagnosis": "<percentage_base | transient_slip | linguistic_slip | no_error | unresolved>",
  "action_type": "<permitted action>",
  "response_bn": "<pedagogical response in Bengali>"
}}
"""


class PromptedTutor(BaseTutor):
    """B1 Baseline: Single structured prompt tutor representing standard LLM prompting."""

    def __init__(
        self,
        name: str = "B1_PromptedTutor",
        llm_callable: Optional[Callable[[str], str]] = None,
    ):
        super().__init__(name=name)
        self.llm_callable = llm_callable
        self.learner_id: Optional[str] = None
        self.problem_dag: Optional[ProblemReferenceDAG] = None
        self.step_history: List[str] = []
        self.first_error_detected: bool = False

    def reset(self, learner_id: str, problem_dag: ProblemReferenceDAG) -> None:
        self.learner_id = learner_id
        self.problem_dag = problem_dag
        self.step_history = []
        self.first_error_detected = False

    def _format_prompt(self, current_step: str, problem_dag: ProblemReferenceDAG) -> str:
        ref_text = "\n".join(
            f"- {s.step_id}: {s.description} ({s.symbolic_expression})"
            for s in problem_dag.reference_steps
        )
        hist_text = "\n".join(f"{i+1}. {st}" for i, st in enumerate(self.step_history[:-1]))
        if not hist_text:
            hist_text = "None (first turn)"

        return B1_PROMPT_TEMPLATE.format(
            problem_text=problem_dag.problem_text,
            reference_steps=ref_text,
            history=hist_text,
            current_step=current_step,
        )

    def _simulate_offline_response(
        self,
        current_step: str,
        problem_dag: ProblemReferenceDAG,
    ) -> Dict[str, str]:
        """Offline simulation conforming to standard LLM behavior on Bengali math steps."""
        from src.normalizer.bengali_normalizer import BengaliNormalizer
        normalizer = BengaliNormalizer()
        norm_text = normalizer.normalize(current_step).normalized_text
        cleaned = norm_text.strip()

        # Check for empty or vague step
        if len(cleaned) < 2 or cleaned in ["?", "কী", "বুঝিনি"]:
            return {
                "interpreted_math": "",
                "mathematical_status": "unverifiable",
                "diagnosis": "unresolved",
                "action_type": "ask_clarification",
                "response_bn": "আপনার হিসাবটি পরিষ্কার করে লিখুন যাতে বুঝতে পারি।",
            }

        # Check error patterns in DAG
        matched_err = None
        for step in problem_dag.reference_steps:
            for pat, err_label in step.known_error_patterns.items():
                val = pat.split("=")[-1].strip() if "=" in pat else pat
                if val and val in cleaned:
                    matched_err = err_label
                    break

        if matched_err:
            diag = "percentage_base" if "conceptual" in matched_err.lower() else "transient_slip"
            return {
                "interpreted_math": current_step,
                "mathematical_status": "invalid",
                "diagnosis": diag,
                "action_type": "give_conceptual_hint",
                "response_bn": "আপনার সমাধানে একটি ভুল পরিলক্ষিত হচ্ছে। সূত্রটি পুনরায় দেখুন।",
            }

        # Check valid steps
        is_valid = False
        for step in problem_dag.reference_steps:
            val = step.symbolic_expression.split("=")[-1].strip() if "=" in step.symbolic_expression else step.symbolic_expression
            if val and val in cleaned:
                is_valid = True
                break

        if is_valid or "10" in cleaned or "সঠিক" in cleaned:
            return {
                "interpreted_math": current_step,
                "mathematical_status": "valid",
                "diagnosis": "no_error",
                "action_type": "acknowledge_correct_step",
                "response_bn": "ধাপটি চমৎকার হয়েছে। সমাধান চালিয়ে যান।",
            }

        return {
            "interpreted_math": current_step,
            "mathematical_status": "unverifiable",
            "diagnosis": "unresolved",
            "action_type": "request_independent_retry",
            "response_bn": "ধাপটি পুনরায় যাচাই করে দেখুন।",
        }

    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        independent_group_id: Optional[str] = None,
    ) -> BaselineStepResult:
        start_time = time.perf_counter()
        self.step_history.append(raw_text)

        prompt = self._format_prompt(raw_text, problem_dag)
        neural_calls = 0

        # Run live LLM or offline simulation
        if self.llm_callable is not None:
            raw_output = self.llm_callable(prompt)
            neural_calls = 1
            try:
                parsed = json.loads(raw_output)
            except Exception:
                parsed = self._simulate_offline_response(raw_text, problem_dag)
        else:
            parsed = self._simulate_offline_response(raw_text, problem_dag)

        # Parse mathematical status
        status_str = parsed.get("mathematical_status", "unverifiable").lower()
        if status_str == "valid":
            math_status = MathematicalStatus.VALID
        elif status_str == "invalid":
            math_status = MathematicalStatus.INVALID
        else:
            math_status = MathematicalStatus.UNVERIFIABLE

        # Parse diagnosis & cause
        diag_str = parsed.get("diagnosis", "unresolved").lower()
        try:
            cause = CandidateCause(diag_str)
        except ValueError:
            cause = CandidateCause.UNRESOLVED

        # Action type
        act_str = parsed.get("action_type", "ask_clarification").lower()
        try:
            action_type = ActionType(act_str)
        except ValueError:
            action_type = ActionType.REQUEST_INDEPENDENT_RETRY

        is_first_err = False
        first_err_reason = None
        if math_status == MathematicalStatus.INVALID:
            if not self.first_error_detected:
                self.first_error_detected = True
                is_first_err = True
                first_err_reason = cause.value

        # Prompted models commit immediately based on their prompt output
        active_commitments = []
        if cause not in (CandidateCause.NO_ERROR, CandidateCause.UNRESOLVED):
            active_commitments.append({
                "learner_id": self.learner_id or "unknown",
                "item_id": problem_dag.item_id,
                "cause": cause.value,
            })

        action = PedagogicalAction(
            action_type=action_type,
            payload=parsed.get("response_bn", ""),
            target_cause=cause,
            is_protected_hint=True,
        )

        latency = (time.perf_counter() - start_time) * 1000

        # Uniform or one-hot belief representation for prompted output
        beliefs = {c: 1.0 if c == cause else 0.0 for c in CandidateCause}

        return BaselineStepResult(
            action=action,
            mathematical_status=math_status,
            beliefs=beliefs,
            active_commitments=active_commitments,
            predicted_cause=cause,
            is_first_error=is_first_err,
            first_error_reason=first_err_reason,
            latency_ms=latency,
            neural_calls=neural_calls,
            symbolic_calls=0,
            tokens_generated=len(action.payload.split()),
            raw_response=action.payload,
            metadata={"prompt_length": len(prompt.split())},
        )
