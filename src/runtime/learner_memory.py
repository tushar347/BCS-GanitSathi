from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from src.controller.diagnostic_controller import DiagnosticController
from src.controller.schemas import ClaimStatus


class LearnerClaimSnapshot(BaseModel):
    cause: str
    probability: float
    status: str
    context: str
    supporting_event_ids: List[str] = Field(default_factory=list)
    contradicting_event_ids: List[str] = Field(default_factory=list)


class LearnerMemory(BaseModel):
    learner_id: str
    total_turns: int = 0
    correct_turns: int = 0
    invalid_turns: int = 0
    assisted_turns: int = 0
    completed_families: List[str] = Field(default_factory=list)
    claims: Dict[str, LearnerClaimSnapshot] = Field(default_factory=dict)


class LearnerMemoryStore:
    def __init__(self):
        self._memories: Dict[str, LearnerMemory] = {}

    def get(self, learner_id: str) -> LearnerMemory:
        if learner_id not in self._memories:
            self._memories[learner_id] = LearnerMemory(learner_id=learner_id)
        return self._memories[learner_id]

    def commit_controller_state(
        self,
        learner_id: str,
        controller: DiagnosticController,
        mathematical_status: str,
        assisted: bool,
        family_id: str,
        completed: bool,
    ) -> LearnerMemory:
        memory = self.get(learner_id)
        memory.total_turns += 1
        if mathematical_status == "valid":
            memory.correct_turns += 1
        elif mathematical_status == "invalid":
            memory.invalid_turns += 1
        if assisted:
            memory.assisted_turns += 1
        if completed and family_id not in memory.completed_families:
            memory.completed_families.append(family_id)
        for cause, hypothesis in controller.belief_updater.active_hypotheses.items():
            if hypothesis.status == ClaimStatus.RETRACTED and cause.value not in memory.claims:
                continue
            memory.claims[cause.value] = LearnerClaimSnapshot(
                cause=cause.value,
                probability=hypothesis.probability,
                status=hypothesis.status.value,
                context=hypothesis.context,
                supporting_event_ids=list(hypothesis.supporting_event_ids),
                contradicting_event_ids=list(hypothesis.contradicting_event_ids),
            )
        return memory
