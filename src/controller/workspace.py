from typing import Dict, List
from src.controller.admission import EvidenceAdmissionPolicy
from src.controller.belief_model import CalibratedBeliefEngine
from src.controller.probe_selector import BoundedProbeSelector
from src.controller.schemas import (
    InstructionalAction,
    LearnerClaim,
    ObservationRecord,
)


class EpistemicControllerWorkspace:
    """
    Epistemic Learning Workspace Controller (§5.1, Appx A.2):
    Integrates admission, calibrated belief updates, and bounded probing.
    """

    def __init__(self):
        self.admission_policy = EvidenceAdmissionPolicy()
        self.belief_engine = CalibratedBeliefEngine()
        self.probe_selector = BoundedProbeSelector()
        self.observations: List[ObservationRecord] = []
        self.active_claims: Dict[str, LearnerClaim] = {}

    def process_student_event(self, record: ObservationRecord) -> InstructionalAction:
        # Step 1: Admission check
        is_admitted = self.admission_policy.evaluate_admission(record, self.observations)
        record.evidence_admitted = is_admitted
        self.observations.append(record)

        if not is_admitted:
            # Unadmitted or unresolved: do not update belief
            return self.probe_selector.select_action(
                item_id=record.item_id,
                hypothesis_probs={"unknown": 1.0},
                top_cause="unresolved",
            )

        # Step 2: Belief update
        claim_key = f"{record.learner_id}_{record.item_id}"
        prior_claim = self.active_claims.get(claim_key)
        updated_claim = self.belief_engine.update_beliefs(
            candidate_causes=record.candidate_causes,
            history=self.observations,
            current_claim=prior_claim,
        )
        self.active_claims[claim_key] = updated_claim

        # Step 3: Action selection
        probs = {c: 0.5 for c in record.candidate_causes} if len(record.candidate_causes) > 1 else {record.candidate_causes[0]: 0.9}
        action = self.probe_selector.select_action(
            item_id=record.item_id,
            hypothesis_probs=probs,
            top_cause=updated_claim.claim_type,
        )
        return action
