from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.controller.schemas import (
    AssistanceLevel,
    CandidateCause,
    ClaimStatus,
    DiagnosticProbe,
    HypothesisRecord,
    MathematicalStatus,
    Observation,
)


DEFAULT_PRIORS: Dict[CandidateCause, float] = {
    CandidateCause.CONCEPTUAL_ERROR: 0.15,
    CandidateCause.PERCENTAGE_BASE: 0.25,
    CandidateCause.TRANSIENT_SLIP: 0.20,
    CandidateCause.LINGUISTIC_SLIP: 0.15,
    CandidateCause.INTERFACE_SLIP: 0.08,
    CandidateCause.NO_ERROR: 0.12,
    CandidateCause.UNRESOLVED: 0.05,
}

LIKELIHOODS_UNASSISTED: Dict[MathematicalStatus, Dict[CandidateCause, float]] = {
    MathematicalStatus.INVALID: {
        CandidateCause.CONCEPTUAL_ERROR: 0.82,
        CandidateCause.PERCENTAGE_BASE: 0.85,
        CandidateCause.TRANSIENT_SLIP: 0.70,
        CandidateCause.LINGUISTIC_SLIP: 0.50,
        CandidateCause.INTERFACE_SLIP: 0.40,
        CandidateCause.NO_ERROR: 0.02,
        CandidateCause.UNRESOLVED: 0.30,
    },
    MathematicalStatus.VALID: {
        CandidateCause.CONCEPTUAL_ERROR: 0.08,
        CandidateCause.PERCENTAGE_BASE: 0.05,
        CandidateCause.TRANSIENT_SLIP: 0.35,
        CandidateCause.LINGUISTIC_SLIP: 0.20,
        CandidateCause.INTERFACE_SLIP: 0.25,
        CandidateCause.NO_ERROR: 0.90,
        CandidateCause.UNRESOLVED: 0.30,
    },
}

LIKELIHOODS_ASSISTED: Dict[MathematicalStatus, Dict[CandidateCause, float]] = {
    MathematicalStatus.VALID: {
        CandidateCause.CONCEPTUAL_ERROR: 0.48,
        CandidateCause.PERCENTAGE_BASE: 0.45,
        CandidateCause.TRANSIENT_SLIP: 0.55,
        CandidateCause.LINGUISTIC_SLIP: 0.45,
        CandidateCause.INTERFACE_SLIP: 0.50,
        CandidateCause.NO_ERROR: 0.50,
        CandidateCause.UNRESOLVED: 0.40,
    },
    MathematicalStatus.INVALID: {
        CandidateCause.CONCEPTUAL_ERROR: 0.88,
        CandidateCause.PERCENTAGE_BASE: 0.90,
        CandidateCause.TRANSIENT_SLIP: 0.60,
        CandidateCause.LINGUISTIC_SLIP: 0.55,
        CandidateCause.INTERFACE_SLIP: 0.45,
        CandidateCause.NO_ERROR: 0.01,
        CandidateCause.UNRESOLVED: 0.35,
    },
}


class CalibratedBeliefUpdater:
    def __init__(
        self,
        activation_threshold: float = 0.80,
        retention_threshold: float = 0.40,
        priors: Optional[Dict[CandidateCause, float]] = None,
    ):
        self.activation_threshold = activation_threshold
        self.retention_threshold = retention_threshold
        self.priors = self._base_priors(priors)
        self.beliefs = self.priors.copy()
        self.active_hypotheses: Dict[CandidateCause, HypothesisRecord] = {}
        self.evidence_groups_per_cause: Dict[CandidateCause, List[str]] = {
            cause: [] for cause in CandidateCause
        }

    def _base_priors(self, priors: Optional[Dict[CandidateCause, float]] = None) -> Dict[CandidateCause, float]:
        values = DEFAULT_PRIORS.copy()
        if priors:
            values.update(priors)
        return {cause: float(values.get(cause, 0.0)) for cause in CandidateCause}

    def set_problem_context(self, *, problem_text: str = "", topic_group: str = "") -> None:
        raw = self._base_priors()
        is_percentage_task = "percentage" in topic_group.lower() or any(token in (problem_text or "").lower() for token in ["%", "শতকরা", "লাভ", "ক্ষতি"])
        if is_percentage_task:
            raw[CandidateCause.PERCENTAGE_BASE] = 0.25
        else:
            raw[CandidateCause.PERCENTAGE_BASE] = 0.0
        normalized_total = sum(raw.values())
        if normalized_total <= 0:
            raw = self._base_priors()
            raw[CandidateCause.PERCENTAGE_BASE] = 0.0
            normalized_total = sum(raw.values())
        self.priors = {cause: value / normalized_total for cause, value in raw.items()}
        self.reset()

    def reset(self):
        self.beliefs = self.priors.copy()
        self.active_hypotheses.clear()
        self.evidence_groups_per_cause = {cause: [] for cause in CandidateCause}

    def update_with_observation(
        self,
        obs: Observation,
        is_first_in_group: bool = True,
    ) -> Dict[CandidateCause, float]:
        if not obs.evidence_admitted or not is_first_in_group:
            return self.beliefs
        is_assisted = obs.assistance_level in (
            AssistanceLevel.KEY_EQUATION_SUPPLIED,
            AssistanceLevel.WORKED_SOLUTION,
        )
        likelihood_table = LIKELIHOODS_ASSISTED if is_assisted else LIKELIHOODS_UNASSISTED
        if obs.mathematical_status not in likelihood_table:
            return self.beliefs
        likelihoods = likelihood_table[obs.mathematical_status]
        unnormalized: Dict[CandidateCause, float] = {}
        for cause in CandidateCause:
            likelihood = likelihoods.get(cause, 0.1)
            if obs.candidate_causes and cause in obs.candidate_causes:
                likelihood *= 1.5
            elif obs.candidate_causes and cause not in obs.candidate_causes and cause != CandidateCause.UNRESOLVED:
                likelihood *= 0.5
            unnormalized[cause] = self.beliefs.get(cause, 0.0) * likelihood
        self._normalize(unnormalized)
        group_id = obs.independent_evidence_group
        if obs.mathematical_status == MathematicalStatus.INVALID:
            supported = set(obs.candidate_causes) or {
                cause for cause in CandidateCause if cause not in (CandidateCause.NO_ERROR, CandidateCause.UNRESOLVED)
            }
            for cause in supported:
                self._add_evidence_group(cause, group_id)
                self._record_support(cause, obs)
        elif obs.mathematical_status == MathematicalStatus.VALID and obs.assistance_level == AssistanceLevel.NONE:
            self._add_evidence_group(CandidateCause.NO_ERROR, group_id)
            for cause in CandidateCause:
                if cause not in (CandidateCause.NO_ERROR, CandidateCause.UNRESOLVED):
                    self._record_contradiction(cause, obs)
        self._govern_claims(obs.learner_id, obs.item_id, obs.assistance_level)
        return self.beliefs

    def update_with_probe_response(
        self,
        probe: DiagnosticProbe,
        response_category: str,
        event_id: str,
        evidence_group: str,
        learner_id: str,
        item_id: str,
        assistance_level: AssistanceLevel = AssistanceLevel.NONE,
    ) -> Dict[CandidateCause, float]:
        if response_category not in probe.response_model:
            return self.beliefs
        likelihoods = probe.response_model[response_category]
        unnormalized = {
            cause: self.beliefs.get(cause, 0.0) * max(float(likelihoods.get(cause, 0.05)), 1e-6)
            for cause in CandidateCause
        }
        self._normalize(unnormalized)
        if likelihoods:
            maximum = max(float(value) for value in likelihoods.values())
            minimum = min(float(value) for value in likelihoods.values())
            for cause in CandidateCause:
                value = float(likelihoods.get(cause, 0.05))
                if maximum > 0 and value >= maximum * 0.8:
                    self._add_evidence_group(cause, evidence_group)
                    self._record_event_id(cause, event_id, support=True, learner_id=learner_id, item_id=item_id, assistance_level=assistance_level)
                elif minimum < maximum and value <= max(minimum * 1.2, 0.10):
                    self._record_event_id(cause, event_id, support=False, learner_id=learner_id, item_id=item_id, assistance_level=assistance_level)
        self._govern_claims(learner_id, item_id, assistance_level)
        return self.beliefs

    def _normalize(self, values: Dict[CandidateCause, float]) -> None:
        total = sum(values.values())
        if total <= 0:
            return
        self.beliefs = {cause: values[cause] / total for cause in CandidateCause}

    def _add_evidence_group(self, cause: CandidateCause, group_id: str) -> None:
        groups = self.evidence_groups_per_cause[cause]
        if group_id not in groups:
            groups.append(group_id)

    def _ensure_hypothesis(
        self,
        cause: CandidateCause,
        learner_id: str,
        item_id: str,
        assistance_level: AssistanceLevel,
    ) -> HypothesisRecord:
        hypothesis = self.active_hypotheses.get(cause)
        if hypothesis is None:
            hypothesis = HypothesisRecord(
                hypothesis_id=f"hyp_{cause.value}",
                learner_id=learner_id,
                skill="bcs_math",
                error_code=cause,
                context=item_id,
                assistance_status=assistance_level,
                probability=self.beliefs[cause],
                status=ClaimStatus.PROVISIONAL,
            )
            self.active_hypotheses[cause] = hypothesis
        return hypothesis

    def _record_support(self, cause: CandidateCause, obs: Observation) -> None:
        hypothesis = self._ensure_hypothesis(cause, obs.learner_id, obs.item_id, obs.assistance_level)
        if obs.event_id not in hypothesis.supporting_event_ids:
            hypothesis.supporting_event_ids.append(obs.event_id)

    def _record_contradiction(self, cause: CandidateCause, obs: Observation) -> None:
        hypothesis = self._ensure_hypothesis(cause, obs.learner_id, obs.item_id, obs.assistance_level)
        if obs.event_id not in hypothesis.contradicting_event_ids:
            hypothesis.contradicting_event_ids.append(obs.event_id)

    def _record_event_id(
        self,
        cause: CandidateCause,
        event_id: str,
        support: bool,
        learner_id: str,
        item_id: str,
        assistance_level: AssistanceLevel,
    ) -> None:
        hypothesis = self._ensure_hypothesis(cause, learner_id, item_id, assistance_level)
        target = hypothesis.supporting_event_ids if support else hypothesis.contradicting_event_ids
        if event_id not in target:
            target.append(event_id)

    def _govern_claims(
        self,
        learner_id: str,
        item_id: str,
        assistance_level: AssistanceLevel,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for cause, probability in self.beliefs.items():
            if cause == CandidateCause.NO_ERROR:
                continue
            hypothesis = self._ensure_hypothesis(cause, learner_id, item_id, assistance_level)
            hypothesis.probability = probability
            hypothesis.latest_update = now
            independent_count = len(self.evidence_groups_per_cause[cause])
            if probability >= self.activation_threshold and independent_count >= 2:
                hypothesis.status = ClaimStatus.ACTIVE
            elif hypothesis.status == ClaimStatus.ACTIVE and (
                hypothesis.contradicting_event_ids or probability < self.activation_threshold
            ):
                hypothesis.status = ClaimStatus.CONTESTED
            if probability < self.retention_threshold and hypothesis.status in (
                ClaimStatus.CONTESTED,
                ClaimStatus.PROVISIONAL,
            ):
                hypothesis.status = ClaimStatus.RETRACTED

    def get_shannon_entropy(self) -> float:
        return -sum(prob * math.log2(prob) for prob in self.beliefs.values() if prob > 1e-9)

    def get_normalized_entropy(self) -> float:
        count = len(self.beliefs)
        if count <= 1:
            return 0.0
        return self.get_shannon_entropy() / math.log2(count)

    def get_top_candidate(self) -> Tuple[CandidateCause, float]:
        return max(self.beliefs.items(), key=lambda item: item[1])
