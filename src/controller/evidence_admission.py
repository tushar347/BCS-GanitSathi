from __future__ import annotations

from typing import Dict, List, Set, Tuple

from src.controller.schemas import InterpretationStatus, MathematicalStatus, Observation


class EvidenceAdmissionManager:
    def __init__(self):
        self.evidence_groups: Dict[str, List[Observation]] = {}
        self.processed_event_ids: Set[str] = set()

    def evaluate_admission(self, obs: Observation) -> Tuple[bool, str]:
        if obs.event_id in self.processed_event_ids:
            return False, "duplicate_event_id"
        if obs.interpretation_status == InterpretationStatus.UNRESOLVED:
            return False, "unresolved_interpretation_logged_without_belief_update"
        if obs.mathematical_status == MathematicalStatus.UNVERIFIABLE:
            return False, "unverifiable_mathematical_step"
        if obs.mathematical_status == MathematicalStatus.INVALID:
            return True, "valid_evidence_of_mathematical_error"
        if obs.mathematical_status == MathematicalStatus.VALID:
            return True, "valid_step_admitted"
        if obs.mathematical_status == MathematicalStatus.UNSUPPORTED:
            return False, "unsupported_alternative_strategy_requires_clarification"
        return False, "unrecognized_observation_criteria"

    def record_and_admit(self, obs: Observation) -> Observation:
        admitted, reason = self.evaluate_admission(obs)
        obs.evidence_admitted = admitted
        obs.verification_reason = f"{obs.verification_reason} [{reason}]".strip()
        self.processed_event_ids.add(obs.event_id)
        if admitted:
            self._append_group(obs)
        return obs

    def record_structured_evidence(self, obs: Observation, reason: str) -> Observation:
        if obs.event_id in self.processed_event_ids:
            obs.evidence_admitted = False
            obs.verification_reason = f"{obs.verification_reason} [duplicate_event_id]".strip()
            return obs
        obs.evidence_admitted = True
        obs.verification_reason = f"{obs.verification_reason} [{reason}]".strip()
        self.processed_event_ids.add(obs.event_id)
        self._append_group(obs)
        return obs

    def _append_group(self, obs: Observation) -> None:
        group = self.evidence_groups.setdefault(obs.independent_evidence_group, [])
        group.append(obs)

    def is_first_in_evidence_group(self, obs: Observation) -> bool:
        group = self.evidence_groups.get(obs.independent_evidence_group, [])
        return len(group) <= 1 or (group and group[0].event_id == obs.event_id)

    def get_independent_evidence_count(self) -> int:
        return len(self.evidence_groups)
