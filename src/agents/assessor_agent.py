from __future__ import annotations

import json
import re
from typing import Iterable, Optional

from src.agents.contracts import AssessmentResult, ProbeResponseAssessment
from src.controller.schemas import AssistanceLevel, CandidateCause, DiagnosticProbe
from src.models.model_gateway import ModelGateway
from src.normalizer.bengali_normalizer import BengaliNormalizer


class AssessorAgent:
    def __init__(self, gateway: Optional[ModelGateway] = None):
        self.gateway = gateway or ModelGateway()
        self.normalizer = BengaliNormalizer()
        self.last_used_model = False

    def assess(
        self,
        problem_text: str,
        student_text: str,
        assistance_level: AssistanceLevel,
        recent_context: Optional[Iterable[str]] = None,
    ) -> AssessmentResult:
        self.last_used_model = False
        if self.gateway.available:
            schema = AssessmentResult.model_json_schema()
            system_prompt = (
                "You are the GonitSathi evidence assessor. Return only JSON matching the supplied schema. "
                "Interpret only observable student evidence. Do not infer a permanent learner trait. "
                "Do not reveal hidden labels, do not solve the problem for the student, and do not write learner state. "
                "Use interpretation_uncertainty as 0 for clear and 1 for highly ambiguous. "
                "Use only these candidate explanations: conceptual_error, percentage_base, transient_slip, linguistic_slip, "
                "interface_slip, no_error, unresolved. Return concise reason_codes, not chain-of-thought."
            )
            user_prompt = json.dumps(
                {
                    "problem": problem_text,
                    "student_text": student_text,
                    "assistance_level": assistance_level.value,
                    "recent_context": list(recent_context or []),
                    "schema": schema,
                },
                ensure_ascii=False,
            )
            result = self.gateway.generate_structured(system_prompt, user_prompt, AssessmentResult)
            if result is not None:
                self.last_used_model = True
                return result
        return self._fallback(student_text)

    def classify_probe_response(
        self,
        problem_text: str,
        probe: DiagnosticProbe,
        student_text: str,
    ) -> ProbeResponseAssessment:
        self.last_used_model = False
        categories = list(probe.response_model.keys())
        if self.gateway.available:
            schema = ProbeResponseAssessment.model_json_schema()
            system_prompt = (
                "You classify an observed response to a diagnostic probe. Return only JSON matching the schema. "
                "Choose response_category only from the supplied categories. Do not diagnose the learner and do not "
                "invent evidence. Return concise evidence spans only."
            )
            user_prompt = json.dumps(
                {
                    "problem": problem_text,
                    "probe": probe.prompt_bn,
                    "student_text": student_text,
                    "allowed_categories": categories,
                    "schema": schema,
                },
                ensure_ascii=False,
            )
            result = self.gateway.generate_structured(system_prompt, user_prompt, ProbeResponseAssessment)
            if result is not None and result.response_category in categories:
                self.last_used_model = True
                return result
        text = student_text.strip()
        if not text:
            category = self._pick_category(categories, ["skipped", "timeout", "ambiguous", "insufficient_evidence"])
            return ProbeResponseAssessment(
                response_category=category,
                evidence_spans=[],
                interpretation_uncertainty=1.0,
                needs_clarification=True,
            )
        lowered = text.lower()
        for category in categories:
            if category.lower() in lowered:
                return ProbeResponseAssessment(
                    response_category=category,
                    evidence_spans=[text],
                    interpretation_uncertainty=0.15,
                    needs_clarification=False,
                )
        category = self._pick_category(categories, ["ambiguous", "insufficient_evidence", "unclear", "other"])
        return ProbeResponseAssessment(
            response_category=category,
            evidence_spans=[text],
            interpretation_uncertainty=0.75,
            needs_clarification=True,
        )

    def _fallback(self, student_text: str) -> AssessmentResult:
        normalized = self.normalizer.normalize(student_text).normalized_text.strip()
        relation = self.normalizer.extract_expression(student_text)
        reason_codes = []
        is_final_answer = False
        numeric_matches = re.findall(r"[-+]?\d+(?:\.\d+)?", normalized)
        has_relation = any(op in relation for op in ["=", "<", ">"])
        compact = normalized.replace(" ", "")
        if not has_relation and numeric_matches and len(compact) <= 32:
            relation = f"answer = {numeric_matches[-1]}"
            is_final_answer = True
            reason_codes.append("short_numeric_answer")
        elif re.search(r"\b(?:answer|ans|final_answer)\b", normalized.lower()):
            is_final_answer = True
            reason_codes.append("explicit_answer_marker")
        elif has_relation:
            reason_codes.append("explicit_relation")
        if not relation or relation in {"?", "??", "???"}:
            return AssessmentResult(
                interpreted_relation="",
                evidence_spans=[student_text] if student_text else [],
                interpretation_uncertainty=0.95,
                candidate_explanations=[CandidateCause.UNRESOLVED],
                needs_clarification=True,
                is_final_answer=False,
                reason_codes=["unresolved_input"],
            )
        candidates = []
        if any(term in student_text for term in ["ভুল", "মনে হয়", "সম্ভবত"]):
            candidates.append(CandidateCause.TRANSIENT_SLIP)
        return AssessmentResult(
            interpreted_relation=relation,
            evidence_spans=[student_text],
            interpretation_uncertainty=0.15 if has_relation or is_final_answer else 0.45,
            candidate_explanations=candidates,
            needs_clarification=False,
            is_final_answer=is_final_answer,
            reason_codes=reason_codes or ["normalized_expression"],
        )

    def _pick_category(self, categories: list[str], preferred: list[str]) -> str:
        lowered = {c.lower(): c for c in categories}
        for name in preferred:
            if name in lowered:
                return lowered[name]
        return categories[-1] if categories else "ambiguous"
