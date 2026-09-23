from __future__ import annotations

import json
from typing import Iterable, Optional

from src.controller.prompt_contracts import RealizerInputContract, RealizerOutputContract
from src.controller.schemas import ActionType, PedagogicalAction
from src.models.model_gateway import ModelGateway


class ExpertAgent:
    def __init__(self, gateway: Optional[ModelGateway] = None):
        self.gateway = gateway or ModelGateway()
        self.last_used_model = False

    def realize(
        self,
        action: PedagogicalAction,
        permitted_facts: Iterable[str],
        recent_context: Optional[Iterable[str]] = None,
        allowed_disclosure_level: str = "protected_hint",
        worked_solution_steps: Optional[Iterable[str]] = None,
        current_problem: Optional[dict] = None,
        student_attempt: Optional[str] = None,
        current_intent: Optional[object] = None,
        **_: object,
    ) -> RealizerOutputContract:
        self.last_used_model = False
        facts = list(permitted_facts)
        context = list(recent_context or [])
        if action.action_type == ActionType.ASK_DIAGNOSTIC_PROBE:
            return RealizerOutputContract(
                bengali_response_text=action.payload,
                cited_fact_ids=[],
                questions_asked_count=1,
                fallback_signal_triggered=False,
            )
        if action.action_type == ActionType.PROVIDE_WORKED_SOLUTION and allowed_disclosure_level == "authorized_worked_example":
            steps = [str(s) for s in worked_solution_steps or [] if str(s).strip()]
            text = "\n".join(steps) if steps else action.payload
            return RealizerOutputContract(
                bengali_response_text=text,
                cited_fact_ids=[],
                questions_asked_count=0,
                fallback_signal_triggered=False,
            )
        if self.gateway.available:
            contract = RealizerInputContract(
                action_type=action.action_type,
                target_cause=action.target_cause,
                permitted_facts=facts,
                recent_dialogue_context=context,
                allowed_disclosure_level=allowed_disclosure_level,
            )
            system_prompt = (
                "You are the GonitSathi expert teaching agent. Return only JSON matching the supplied schema. "
                "You may express only the controller-authorized action and supplied facts. Do not change the diagnosis, "
                "do not write learner state, and do not reveal a final answer or decisive calculation in protected_hint mode. "
                "Use clear, short, natural Bengali and ask at most one question."
            )
            user_prompt = json.dumps(
                {
                    "input": contract.model_dump(mode="json"),
                    "schema": RealizerOutputContract.model_json_schema(),
                    "controller_payload": action.payload,
                },
                ensure_ascii=False,
            )
            result = self.gateway.generate_structured(system_prompt, user_prompt, RealizerOutputContract)
            if result is not None:
                self.last_used_model = True
                return result
        return RealizerOutputContract(
            bengali_response_text=action.payload,
            cited_fact_ids=[],
            questions_asked_count=1 if "?" in action.payload or "?" in action.payload else 0,
            fallback_signal_triggered=False,
        )
