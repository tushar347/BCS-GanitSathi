from __future__ import annotations

import math
from typing import Any, Dict, Optional

from pydantic import BaseModel

from src.agents.assessor_agent import AssessorAgent
from src.agents.contracts import (
    AgenticCycleRecord,
    AgentTurnTrace,
    CurriculumDecision,
    MotivationDecision,
    ReflectionRecord,
)
from src.agents.curriculum_agent import CurriculumAgent
from src.agents.expert_agent import ExpertAgent
from src.agents.motivational_agent import MotivationalAgent
from src.controller.diagnostic_controller import DiagnosticController
from src.controller.schemas import ActionType, AssistanceLevel, MathematicalStatus, PedagogicalAction, StudentIntent
from src.models.model_gateway import ModelGateway
from src.runtime.learner_memory import LearnerMemoryStore
from src.runtime.research_repository import ResearchBenchmarkRepository
from src.runtime.session_state import SessionTurn, TutoringSessionState


class AgenticTurnResult(BaseModel):
    released_text: str
    action: PedagogicalAction
    observation: Dict[str, Any]
    beliefs: Dict[str, float]
    active_claims: Dict[str, Dict[str, Any]]
    motivation: MotivationDecision
    curriculum: Optional[CurriculumDecision] = None
    next_question: Optional[Dict[str, Any]] = None
    trace: AgentTurnTrace
    cycle: AgenticCycleRecord
    session: TutoringSessionState


class AgenticTutoringOrchestrator:
    def __init__(
        self,
        repository: Optional[ResearchBenchmarkRepository] = None,
        gateway: Optional[ModelGateway] = None,
        activation_threshold: float = 0.80,
        retention_threshold: float = 0.40,
        entropy_threshold: float = 0.40,
        max_probes_per_problem: int = 1,
    ):
        self.repository = repository or ResearchBenchmarkRepository()
        self.gateway = gateway or ModelGateway()
        self.assessor = AssessorAgent(self.gateway)
        self.expert = ExpertAgent(self.gateway)
        self.curriculum = CurriculumAgent()
        self.motivational = MotivationalAgent()
        self.memory = LearnerMemoryStore()
        self.controller = DiagnosticController(
            activation_threshold=activation_threshold,
            retention_threshold=retention_threshold,
            entropy_threshold=entropy_threshold,
            max_probes_per_problem=max_probes_per_problem,
        )
        self.session: Optional[TutoringSessionState] = None
        self.problem_dag = None

    def start_session(self, learner_id: str, item_id: str) -> TutoringSessionState:
        context = self.repository.get_context(item_id)
        self.problem_dag = self.repository.build_problem_dag(item_id)
        self.controller.reset_episode()
        self.controller.set_problem_context(problem_text=context.problem.get("question_original", ""), topic_group=str(context.problem.get("topic_group", "")))
        self.session = TutoringSessionState(
            learner_id=learner_id,
            item_id=item_id,
            family_id=str(context.problem.get("family_id", item_id)),
            seen_families=[str(context.problem.get("family_id", item_id))],
        )
        return self.session

    def submit(
        self,
        student_text: str,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
    ) -> AgenticTurnResult:
        if self.session is None or self.problem_dag is None:
            raise RuntimeError("start_session must be called before submit")
        session = self.session
        context = self.repository.get_context(session.item_id)
        calls_before = self.gateway.call_count
        recent_context = self._recent_context()
        probe_response_category = None
        previous_beliefs = dict(self.controller.belief_updater.beliefs)
        previous_uncertainty = self._entropy(previous_beliefs)
        was_probe_response = session.pending_probe is not None
        intent = self._classify_student_intent(student_text)
        if session.pending_probe is not None:
            probe_assessment = self.assessor.classify_probe_response(
                problem_text=self.problem_dag.problem_text,
                probe=session.pending_probe,
                student_text=student_text,
            )
            probe_response_category = probe_assessment.response_category
            action, _, obs = self.controller.process_probe_response(
                raw_text=student_text,
                response_category=probe_assessment.response_category,
                probe=session.pending_probe,
                problem_dag=self.problem_dag,
                learner_id=session.learner_id,
                assistance_level=assistance_level,
                prohibited_answers=self.repository.prohibited_answers(session.item_id),
                interpretation_uncertainty=probe_assessment.interpretation_uncertainty,
            )
            session.pending_probe = None
            session.pending_probe_item_id = None
            assessor_reason_codes = [f"probe_response:{probe_assessment.response_category}"]
            reason_payload = probe_assessment.model_dump(mode="json")
        elif intent == StudentIntent.CLARIFICATION_QUESTION:
            action, _, obs = self.controller.process_clarification_question(
                raw_text=student_text,
                problem_dag=self.problem_dag,
                learner_id=session.learner_id,
                assistance_level=assistance_level,
            )
            assessor_reason_codes = ["clarification_question"]
            reason_payload = {"intent": intent.value, "event_type": "clarification_question"}
            probe_response_category = None
        else:
            assessment = self.assessor.assess(
                problem_text=self.problem_dag.problem_text,
                student_text=student_text,
                assistance_level=assistance_level,
                recent_context=recent_context,
            )
            action, _, obs = self.controller.process_student_step(
                raw_text=student_text,
                problem_dag=self.problem_dag,
                learner_id=session.learner_id,
                assistance_level=assistance_level,
                candidate_probes=self.repository.build_diagnostic_probes(session.item_id),
                prohibited_answers=self.repository.prohibited_answers(session.item_id),
                interpreted_relation=assessment.interpreted_relation,
                candidate_causes_override=assessment.candidate_explanations,
                interpretation_uncertainty=assessment.interpretation_uncertainty,
                needs_clarification=assessment.needs_clarification,
            )
            assessor_reason_codes = assessment.reason_codes
            reason_payload = assessment.model_dump(mode="json")
        action = self._enforce_output_policy(action)
        disclosure = self._disclosure_level(action)
        realized = self.expert.realize(
            action=action,
            permitted_facts=self.repository.permitted_facts(session.item_id),
            recent_context=recent_context,
            allowed_disclosure_level=disclosure,
            worked_solution_steps=self.repository.worked_solution_steps(session.item_id),
            current_problem=context.problem,
            student_attempt=student_text,
            current_intent=intent,
        )
        audit = self.controller.audit_generated_response(
            action,
            realized.bengali_response_text,
            prohibited_answers=self.repository.prohibited_answers(session.item_id),
        )
        previous_errors = session.consecutive_errors
        if obs.mathematical_status == MathematicalStatus.VALID:
            session.consecutive_successes += 1
            session.consecutive_errors = 0
        elif obs.mathematical_status == MathematicalStatus.INVALID:
            session.consecutive_errors += 1
            session.consecutive_successes = 0
        recovered = previous_errors > 0 and obs.mathematical_status == MathematicalStatus.VALID
        motivation = self.motivational.decide(
            mathematical_status=obs.mathematical_status,
            consecutive_errors=session.consecutive_errors,
            consecutive_successes=session.consecutive_successes,
            recovered_after_help=recovered,
        )
        released_text = audit.released_text
        if motivation.should_include:
            released_text = f"{released_text}\n\n{motivation.message}"
        curriculum_decision = None
        next_question = None
        completed = self._is_problem_complete(obs)
        if completed:
            curriculum_decision = self.curriculum.recommend_next(
                current_problem=context.problem,
                candidate_problems=self.repository.list_problems(),
                seen_families=set(session.seen_families),
                beliefs=self.controller.belief_updater.beliefs,
            )
            if curriculum_decision.item_id:
                next_context = self.repository.get_context(curriculum_decision.item_id)
                next_question = next_context.problem
        if action.action_type == ActionType.ASK_DIAGNOSTIC_PROBE and action.probe is not None:
            session.pending_probe = action.probe
            session.pending_probe_item_id = session.item_id
        session.turn_index += 1
        session.last_assistance_level = assistance_level
        if session.family_id not in session.seen_families:
            session.seen_families.append(session.family_id)
        beliefs = {cause.value: round(value, 6) for cause, value in self.controller.belief_updater.beliefs.items()}
        active_claims = {
            cause.value: hypothesis.model_dump(mode="json")
            for cause, hypothesis in self.controller.belief_updater.active_hypotheses.items()
        }
        self.memory.commit_controller_state(
            learner_id=session.learner_id,
            controller=self.controller,
            mathematical_status=obs.mathematical_status.value,
            assisted=assistance_level != AssistanceLevel.NONE,
            family_id=session.family_id,
            completed=completed,
        )
        current_uncertainty = self._entropy(self.controller.belief_updater.beliefs)
        reflection = ReflectionRecord(
            previous_uncertainty=round(previous_uncertainty, 6),
            current_uncertainty=round(current_uncertainty, 6),
            uncertainty_change=round(previous_uncertainty - current_uncertainty, 6),
            outcome=self._reflection_outcome(obs.mathematical_status, was_probe_response, previous_uncertainty, current_uncertainty),
            next_action=action.action_type.value,
            state_changed=previous_beliefs != self.controller.belief_updater.beliefs,
        )
        trace = AgentTurnTrace(
            assessor_used_model=self.assessor.last_used_model,
            expert_used_model=self.expert.last_used_model,
            curriculum_invoked=curriculum_decision is not None,
            motivation_invoked=True,
            action_type=action.action_type,
            mathematical_status=obs.mathematical_status,
            probe_response_category=probe_response_category,
            reason_codes=assessor_reason_codes,
            costs={"neural_calls": self.gateway.call_count - calls_before, "symbolic_calls": 0 if probe_response_category else 1},
        )
        cycle = AgenticCycleRecord(
            observe={
                "student_text": student_text,
                "event_type": obs.event_type,
                "assistance_level": assistance_level.value,
                "item_id": session.item_id,
            },
            reason={
                "assessment": reason_payload,
                "beliefs_before": {cause.value: round(value, 6) for cause, value in previous_beliefs.items()},
                "beliefs_after": beliefs,
            },
            plan={
                "action_type": action.action_type.value,
                "probe_selected": action.probe.probe_id if action.probe else None,
                "disclosure_level": disclosure,
            },
            act={
                "released_text": released_text,
                "motivation": motivation.model_dump(),
                "curriculum": curriculum_decision.model_dump() if curriculum_decision else None,
            },
            reflect=reflection,
        )
        session.turns.append(
            SessionTurn(
                turn_index=session.turn_index,
                student_text=student_text,
                released_text=released_text,
                item_id=session.item_id,
                action_type=action.action_type.value,
                mathematical_status=obs.mathematical_status.value,
                beliefs=beliefs,
                metadata={
                    "intent": intent.value,
                    "event_type": obs.event_type,
                    "probe_response_category": probe_response_category,
                    "curriculum": curriculum_decision.model_dump() if curriculum_decision else None,
                    "motivation": motivation.model_dump(),
                    "neural_calls": trace.costs["neural_calls"],
                },
            )
        )
        return AgenticTurnResult(
            released_text=released_text,
            action=action,
            observation=obs.model_dump(mode="json"),
            beliefs=beliefs,
            active_claims=active_claims,
            motivation=motivation,
            curriculum=curriculum_decision,
            next_question=next_question,
            trace=trace,
            cycle=cycle,
            session=session,
        )

    def move_to_question(self, item_id: str) -> TutoringSessionState:
        if self.session is None:
            raise RuntimeError("No active session")
        learner_id = self.session.learner_id
        seen = list(self.session.seen_families)
        context = self.repository.get_context(item_id)
        family_id = str(context.problem.get("family_id", item_id))
        if family_id not in seen:
            seen.append(family_id)
        self.problem_dag = self.repository.build_problem_dag(item_id)
        self.controller.reset_episode()
        self.controller.set_problem_context(problem_text=context.problem.get("question_original", ""), topic_group=str(context.problem.get("topic_group", "")))
        self.session = TutoringSessionState(
            learner_id=learner_id,
            item_id=item_id,
            family_id=family_id,
            seen_families=seen,
        )
        return self.session

    def request_worked_solution(self) -> str:
        if self.session is None:
            raise RuntimeError("No active session")
        action = PedagogicalAction(
            action_type=ActionType.PROVIDE_WORKED_SOLUTION,
            payload="সমাধানটি ধাপে ধাপে দেখানো হচ্ছে।",
            is_protected_hint=False,
        )
        realized = self.expert.realize(
            action=action,
            permitted_facts=self.repository.permitted_facts(self.session.item_id),
            recent_context=self._recent_context(),
            allowed_disclosure_level="authorized_worked_example",
            worked_solution_steps=self.repository.worked_solution_steps(self.session.item_id),
        )
        return realized.bengali_response_text

    def _enforce_output_policy(self, action: PedagogicalAction) -> PedagogicalAction:
        if self.session is None:
            return action
        if action.action_type == ActionType.ASK_CLARIFICATION:
            return action
        if self.repository.policy_allows(self.session.item_id, action.action_type.value):
            return action
        context = self.repository.get_context(self.session.item_id)
        permitted = {str(value) for value in context.output_policy.get("permitted_action", [])}
        if "ask_diagnostic_probe" in permitted and action.probe is not None:
            return PedagogicalAction(
                action_type=ActionType.ASK_DIAGNOSTIC_PROBE,
                payload=action.probe.prompt_bn,
                probe=action.probe,
                target_cause=action.target_cause,
            )
        if "acknowledge_valid_step" in permitted and action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP:
            return action
        return PedagogicalAction(
            action_type=ActionType.OFFER_LOCAL_SCAFFOLD,
            payload="চূড়ান্ত উত্তর না বলে, ব্যবহৃত নিয়ম এবং পরের ছোট ধাপটি আবার যাচাই করো।",
            target_cause=action.target_cause,
        )

    def _disclosure_level(self, action: PedagogicalAction) -> str:
        if action.action_type == ActionType.PROVIDE_WORKED_SOLUTION:
            return "authorized_worked_example"
        return "protected_hint"

    def _classify_student_intent(self, student_text: str) -> StudentIntent:
        text = (student_text or "").strip()
        if not text:
            return StudentIntent.SKIP
        lowered = text.lower()
        if "skip" in lowered or lowered in {"skip", "pass", "বাতিল"}:
            return StudentIntent.SKIP
        if lowered in {"yes", "হ্যাঁ", "জি", "ঠিক", "ঠিক আছে"}:
            return StudentIntent.CONFIRMATION
        if any(token in lowered for token in ["hint", "টিপস", "tip", "কিছু_hint", "একটু_help", "সাহায্য", "দাও"]):
            return StudentIntent.REQUEST_HINT
        if any(token in lowered for token in ["solution", "সমাধান", "final answer", "উত্তর দেখাও", "show solution"]):
            return StudentIntent.REQUEST_SOLUTION
        if any(token in lowered for token in ["কেন", "why", "কিভাবে", "how", "মানে", "explain", "ব্যাখ্যা", "কি", "কী"]) and ("?" in text or any(token in lowered for token in ["কী", "কি", "কেন", "ব্যাখ্যা", "explain"])):
            return StudentIntent.CLARIFICATION_QUESTION
        if any(token in lowered for token in ["explain", "ব্যাখ্যা", "why", "কেন"]) and "?" not in text:
            return StudentIntent.REQUEST_EXPLANATION
        if any(ch.isdigit() for ch in text) or any(op in lowered for op in ["+", "-", "*", "x", "=", "%", "/", ".", "অথবা"]):
            return StudentIntent.ATTEMPT
        if any(word in lowered for word in ["status", "meta", "metadata", "system", "debug"]):
            return StudentIntent.META
        return StudentIntent.UNKNOWN

    def _recent_context(self) -> list[str]:
        if self.session is None:
            return []
        values = []
        for turn in self.session.turns[-4:]:
            values.append(f"student: {turn.student_text}")
            values.append(f"tutor: {turn.released_text}")
        return values


    def _entropy(self, beliefs) -> float:
        values = [float(value) for value in beliefs.values() if float(value) > 1e-12]
        if len(values) <= 1:
            return 0.0
        raw = -sum(value * math.log2(value) for value in values)
        return raw / math.log2(len(values))

    def _reflection_outcome(
        self,
        status: MathematicalStatus,
        was_probe_response: bool,
        previous_uncertainty: float,
        current_uncertainty: float,
    ) -> str:
        if was_probe_response:
            if current_uncertainty + 1e-6 < previous_uncertainty:
                return "probe_reduced_uncertainty"
            return "probe_did_not_reduce_uncertainty"
        if status == MathematicalStatus.VALID:
            return "successful_observed_step"
        if status == MathematicalStatus.INVALID:
            return "error_evidence_updated"
        return "clarification_or_unsupported_evidence"

    def _is_problem_complete(self, obs) -> bool:
        if obs.mathematical_status != MathematicalStatus.VALID:
            return False
        return "accepted_final_answer" in obs.verification_reason or "final_answer" in obs.verification_reason
