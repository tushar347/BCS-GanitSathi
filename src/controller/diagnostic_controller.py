from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Tuple

from src.controller.belief_updater import CalibratedBeliefUpdater
from src.controller.evidence_admission import EvidenceAdmissionManager
from src.controller.guardrail import AuditResult, PedagogicalGuardrail
from src.controller.probe_selector import ProbeSelector
from src.controller.schemas import (
    ActionType,
    AssistanceLevel,
    CandidateCause,
    DiagnosticProbe,
    InterpretationStatus,
    MathematicalStatus,
    Observation,
    PedagogicalAction,
)
from src.normalizer.bengali_normalizer import BengaliNormalizer
from src.verifier.symbolic_verifier import ProblemReferenceDAG, SymbolicVerifier, VerificationResult


class DiagnosticController:
    def __init__(
        self,
        activation_threshold: float = 0.80,
        retention_threshold: float = 0.40,
        entropy_threshold: float = 0.40,
        max_probes_per_problem: int = 1,
    ):
        self.normalizer = BengaliNormalizer()
        self.verifier = SymbolicVerifier()
        self.admission_mgr = EvidenceAdmissionManager()
        self.belief_updater = CalibratedBeliefUpdater(
            activation_threshold=activation_threshold,
            retention_threshold=retention_threshold,
        )
        self.probe_selector = ProbeSelector(
            entropy_threshold=entropy_threshold,
            max_probes_per_problem=max_probes_per_problem,
        )
        self.guardrail = PedagogicalGuardrail()
        self.observation_log: List[Observation] = []
        self.audit_log: List[Dict] = []

    def reset_episode(self):
        self.belief_updater.reset()
        self.probe_selector.reset_episode()
        self.admission_mgr = EvidenceAdmissionManager()

    def set_problem_context(self, problem_text: str = "", topic_group: str = "") -> None:
        self.belief_updater.set_problem_context(problem_text=problem_text, topic_group=topic_group)

    def process_student_step(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        learner_id: str = "learner_01",
        independent_group_id: Optional[str] = None,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        candidate_probes: Optional[List[DiagnosticProbe]] = None,
        prohibited_answers: Optional[List[str]] = None,
        decisive_calculations: Optional[List[str]] = None,
        interpreted_relation: Optional[str] = None,
        candidate_causes_override: Optional[List[CandidateCause]] = None,
        interpretation_uncertainty: float = 0.0,
        needs_clarification: bool = False,
        event_type: str = "student_step",
        source_type: str = "independent_practice",
    ) -> Tuple[PedagogicalAction, AuditResult, Observation]:
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        group_id = independent_group_id or f"grp_{uuid.uuid4().hex[:8]}"
        norm_result = self.normalizer.normalize(raw_text)
        expression = interpreted_relation
        if expression is None:
            expression = self.normalizer.extract_expression(
                norm_result.normalized_text,
                variable_aliases=getattr(problem_dag, "variable_aliases", None),
            )
        if needs_clarification or interpretation_uncertainty >= 0.85 or not expression:
            verification = VerificationResult(
                mathematical_status=MathematicalStatus.UNVERIFIABLE,
                interpretation_status=InterpretationStatus.UNRESOLVED,
                verification_reason="assessor_requested_clarification",
                normalized_expression=expression or "",
            )
        else:
            verification = self.verifier.verify_step(
                student_expression=expression,
                problem_dag=problem_dag,
            )
        candidate_causes = self._candidate_causes(
            verification=verification,
            problem_text=problem_dag.problem_text,
            overrides=candidate_causes_override or [],
        )
        obs = Observation(
            event_id=event_id,
            learner_id=learner_id,
            item_id=problem_dag.item_id,
            family_id=problem_dag.family_id,
            independent_evidence_group=group_id,
            event_type=event_type,
            original_text=raw_text,
            normalized_text=norm_result.normalized_text,
            assistance_level=assistance_level,
            source_type=source_type,
            interpretation_status=verification.interpretation_status,
            interpretation_uncertainty=interpretation_uncertainty,
            mathematical_status=verification.mathematical_status,
            verification_reason=verification.verification_reason,
            candidate_causes=candidate_causes,
        )
        obs = self.admission_mgr.record_and_admit(obs)
        is_first_in_group = self.admission_mgr.is_first_in_evidence_group(obs)
        self.observation_log.append(obs)
        if obs.evidence_admitted:
            self.belief_updater.update_with_observation(obs, is_first_in_group=is_first_in_group)
            action = self._select_action(verification.mathematical_status, candidate_probes or [])
        else:
            action = PedagogicalAction(
                action_type=ActionType.ASK_CLARIFICATION,
                payload="আপনার হিসাবের ধাপটি আরেকবার স্পষ্টভাবে লিখে বা বুঝিয়ে বলুন।",
            )
        audit = self.audit_generated_response(
            action,
            action.payload,
            prohibited_answers=prohibited_answers,
            decisive_calculations=decisive_calculations,
        )
        self._record_audit(event_id, obs, action, audit)
        return action, audit, obs

    def process_clarification_question(
        self,
        raw_text: str,
        problem_dag: ProblemReferenceDAG,
        learner_id: str = "learner_01",
        independent_group_id: Optional[str] = None,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        prohibited_answers: Optional[List[str]] = None,
        decisive_calculations: Optional[List[str]] = None,
    ) -> Tuple[PedagogicalAction, AuditResult, Observation]:
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        group_id = independent_group_id or f"clarify_{uuid.uuid4().hex[:8]}"
        norm_result = self.normalizer.normalize(raw_text)
        obs = Observation(
            event_id=event_id,
            learner_id=learner_id,
            item_id=problem_dag.item_id,
            family_id=problem_dag.family_id,
            independent_evidence_group=group_id,
            event_type="clarification_question",
            original_text=raw_text,
            normalized_text=norm_result.normalized_text,
            assistance_level=assistance_level,
            source_type="clarification",
            interpretation_status=InterpretationStatus.UNRESOLVED,
            interpretation_uncertainty=1.0,
            mathematical_status=MathematicalStatus.UNVERIFIABLE,
            verification_reason="clarification_question_only",
            candidate_causes=[CandidateCause.UNRESOLVED],
            evidence_admitted=False,
        )
        self.observation_log.append(obs)
        action = PedagogicalAction(
            action_type=ActionType.ASK_CLARIFICATION,
            payload="১ মৌলিক সংখ্যা নয়। মৌলিক সংখ্যা হলো ১-এর চেয়ে বড় এমন সংখ্যা, যা ১ এবং নিজেই ছাড়া অন্য কোনো সংখ্যা দিয়ে ভাগ যায় না।",
            target_cause=CandidateCause.UNRESOLVED,
        )
        audit = self.audit_generated_response(
            action,
            action.payload,
            prohibited_answers=prohibited_answers,
            decisive_calculations=decisive_calculations,
        )
        self._record_audit(event_id, obs, action, audit)
        return action, audit, obs

    def process_probe_response(
        self,
        raw_text: str,
        response_category: str,
        probe: DiagnosticProbe,
        problem_dag: ProblemReferenceDAG,
        learner_id: str = "learner_01",
        independent_group_id: Optional[str] = None,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
        prohibited_answers: Optional[List[str]] = None,
        decisive_calculations: Optional[List[str]] = None,
        interpretation_uncertainty: float = 0.0,
    ) -> Tuple[PedagogicalAction, AuditResult, Observation]:
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        group_id = independent_group_id or f"probe_{uuid.uuid4().hex[:8]}"
        norm_result = self.normalizer.normalize(raw_text)
        likelihoods = probe.response_model.get(response_category, {})
        ranked = sorted(likelihoods.items(), key=lambda item: item[1], reverse=True)
        candidate_causes = [cause for cause, _ in ranked[:2]]
        obs = Observation(
            event_id=event_id,
            learner_id=learner_id,
            item_id=problem_dag.item_id,
            family_id=problem_dag.family_id,
            independent_evidence_group=group_id,
            event_type="probe_response",
            original_text=raw_text,
            normalized_text=norm_result.normalized_text,
            assistance_level=assistance_level,
            source_type="diagnostic_probe",
            interpretation_status=InterpretationStatus.SUPPORTED,
            interpretation_uncertainty=interpretation_uncertainty,
            mathematical_status=MathematicalStatus.UNSUPPORTED,
            verification_reason=f"probe_response:{response_category}",
            candidate_causes=candidate_causes,
        )
        obs = self.admission_mgr.record_structured_evidence(obs, "observed_probe_response")
        self.observation_log.append(obs)
        if obs.evidence_admitted and response_category in probe.response_model:
            self.belief_updater.update_with_probe_response(
                probe=probe,
                response_category=response_category,
                event_id=event_id,
                evidence_group=group_id,
                learner_id=learner_id,
                item_id=problem_dag.item_id,
                assistance_level=assistance_level,
            )
            action = self._teaching_action_from_belief()
        else:
            action = PedagogicalAction(
                action_type=ActionType.ASK_CLARIFICATION,
                payload="প্রশ্নটির উত্তরে তুমি কী বোঝাতে চেয়েছ, এক লাইনে আরেকবার বলো।",
            )
        audit = self.audit_generated_response(
            action,
            action.payload,
            prohibited_answers=prohibited_answers,
            decisive_calculations=decisive_calculations,
        )
        self._record_audit(event_id, obs, action, audit)
        return action, audit, obs

    def audit_generated_response(
        self,
        action: PedagogicalAction,
        raw_text: str,
        prohibited_answers: Optional[List[str]] = None,
        decisive_calculations: Optional[List[str]] = None,
    ) -> AuditResult:
        return self.guardrail.audit_response(
            action=action,
            raw_text=raw_text,
            prohibited_final_answers=prohibited_answers or [],
            decisive_calculations=decisive_calculations or [],
        )

    def _candidate_causes(
        self,
        verification: VerificationResult,
        problem_text: str,
        overrides: List[CandidateCause],
    ) -> List[CandidateCause]:
        causes = list(dict.fromkeys(overrides))
        if verification.mathematical_status == MathematicalStatus.VALID:
            causes.append(CandidateCause.NO_ERROR)
        elif verification.mathematical_status == MathematicalStatus.INVALID:
            reason = verification.verification_reason.lower()
            percentage_context = any(token in problem_text for token in ["%", "শতকরা", "লাভ", "ক্ষতি"])
            if "percentage_base" in reason or percentage_context:
                causes.append(CandidateCause.PERCENTAGE_BASE)
            else:
                causes.append(CandidateCause.CONCEPTUAL_ERROR)
            causes.append(CandidateCause.TRANSIENT_SLIP)
        elif verification.interpretation_status == InterpretationStatus.UNRESOLVED:
            causes.append(CandidateCause.UNRESOLVED)
        return list(dict.fromkeys(causes))

    def _select_action(
        self,
        mathematical_status: MathematicalStatus,
        candidate_probes: List[DiagnosticProbe],
    ) -> PedagogicalAction:
        if mathematical_status == MathematicalStatus.INVALID and candidate_probes:
            selected_probe = self.probe_selector.select_probe(
                candidate_probes=candidate_probes,
                current_beliefs=self.belief_updater.beliefs,
                normalized_entropy=self.belief_updater.get_normalized_entropy(),
            )
            if selected_probe is not None:
                return PedagogicalAction(
                    action_type=ActionType.ASK_DIAGNOSTIC_PROBE,
                    payload=selected_probe.prompt_bn,
                    probe=selected_probe,
                    target_cause=selected_probe.candidate_causes[0] if selected_probe.candidate_causes else None,
                )
        if mathematical_status == MathematicalStatus.VALID:
            return PedagogicalAction(
                action_type=ActionType.ACKNOWLEDGE_CORRECT_STEP,
                payload="এই ধাপটি সঠিক হয়েছে। এবার পরের ধাপটি নিজে চেষ্টা করো।",
                target_cause=CandidateCause.NO_ERROR,
            )
        return self._teaching_action_from_belief()

    def _teaching_action_from_belief(self) -> PedagogicalAction:
        top_cause, top_probability = self.belief_updater.get_top_candidate()
        if top_cause in (CandidateCause.PERCENTAGE_BASE, CandidateCause.CONCEPTUAL_ERROR) and top_probability >= 0.5:
            payload = "যে নিয়ম বা সম্পর্কটি ব্যবহার করছ, সেটি এই সমস্যায় কেন প্রযোজ্য তা আগে যাচাই করো।"
            if top_cause == CandidateCause.PERCENTAGE_BASE:
                payload = "শতকরা পরিবর্তনের ক্ষেত্রে কোন রাশিটিকে ভিত্তি ধরা হচ্ছে, সেটি আগে চিহ্নিত করো।"
            return PedagogicalAction(
                action_type=ActionType.GIVE_CONCEPTUAL_HINT,
                payload=payload,
                target_cause=top_cause,
            )
        if top_cause == CandidateCause.NO_ERROR:
            return PedagogicalAction(
                action_type=ActionType.REQUEST_INDEPENDENT_RETRY,
                payload="এবার একই ধারণাটি সাহায্য ছাড়া আরেকটি ধাপে প্রয়োগ করে দেখো।",
                target_cause=top_cause,
            )
        if top_cause == CandidateCause.UNRESOLVED:
            return PedagogicalAction(
                action_type=ActionType.ASK_CLARIFICATION,
                payload="তুমি কোন নিয়ম ব্যবহার করেছ, সেটি এক লাইনে স্পষ্ট করে বলো।",
                target_cause=top_cause,
            )
        return PedagogicalAction(
            action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
            payload="সমস্যার জানা রাশি, অজানা রাশি এবং তাদের সম্পর্কটি আগে লিখে তারপর হিসাবটি আবার করো।",
            target_cause=top_cause,
        )

    def _record_audit(
        self,
        event_id: str,
        obs: Observation,
        action: PedagogicalAction,
        audit: AuditResult,
    ) -> None:
        self.audit_log.append(
            {
                "event_id": event_id,
                "observation": obs.model_dump(),
                "action": action.model_dump(exclude={"probe": {"response_model"}} if action.probe else None),
                "audit": audit.__dict__,
                "beliefs": {cause.value: round(value, 4) for cause, value in self.belief_updater.beliefs.items()},
            }
        )
