from typing import Dict, List, Optional
from src.controller.schemas import (
    AssistanceLevel,
    ClaimStatus,
    LearnerClaim,
    MathematicalStatus,
    ObservationRecord,
)


class CalibratedBeliefEngine:
    """
    Calibrated Belief Engine (§5.4, §5.5):
    Maintains categorical belief across competing error causes.
    Controls claim state transitions: provisional -> active -> contested -> retracted.
    """

    def __init__(
        self,
        theta_commit: float = 0.80,
        theta_provisional: float = 0.45,
        theta_retract: float = 0.25,
    ):
        self.theta_commit = theta_commit
        self.theta_provisional = theta_provisional
        self.theta_retract = theta_retract

    def update_beliefs(
        self,
        candidate_causes: List[str],
        history: List[ObservationRecord],
        current_claim: Optional[LearnerClaim] = None,
    ) -> LearnerClaim:
        """
        Computes evidence-weighted posterior belief for candidate causes
        and determines claim promotion or retraction.
        """
        if not candidate_causes:
            candidate_causes = ["transient_slip"]

        # Track evidence counts weighted by assistance
        support_weights: Dict[str, float] = {c: 0.1 for c in candidate_causes}  # Laplace prior
        support_weights["independent_mastery"] = 0.1
        contradictions = []
        supporting_event_ids = []

        for obs in history:
            if not obs.evidence_admitted:
                continue

            discount = 1.0
            if obs.assistance_level == AssistanceLevel.HINT:
                discount = 0.5
            elif obs.assistance_level == AssistanceLevel.SUPPLIED_EQUATION:
                discount = 0.2
            elif obs.assistance_level == AssistanceLevel.DIRECT_ANSWER:
                discount = 0.0

            if obs.mathematical_status == MathematicalStatus.INVALID:
                # Wrong step supports candidate causes
                for cause in obs.candidate_causes:
                    if cause in support_weights:
                        support_weights[cause] += 1.0 * discount
                        supporting_event_ids.append(obs.event_id)
            elif obs.mathematical_status == MathematicalStatus.VALID:
                # Correct step provides evidence towards mastery
                # An assisted correct answer contributes much less to independent mastery
                support_weights["independent_mastery"] += 1.5 * discount
                if discount > 0.8:  # Independent correct step contradicts prior error claim
                    contradictions.append(obs.event_id)

        # Normalize to categorical probabilities
        total = sum(support_weights.values())
        probs = {k: v / total for k, v in support_weights.items()}

        # Top diagnostic cause (excluding independent_mastery)
        diagnostic_causes = [c for c in candidate_causes if c in probs]
        if not diagnostic_causes:
            top_cause = "transient_slip"
            top_prob = 0.0
        else:
            top_cause = max(diagnostic_causes, key=lambda c: probs[c])
            top_prob = probs[top_cause]

        # Determine Claim Status
        status = ClaimStatus.PROVISIONAL
        if top_prob >= self.theta_commit and len(contradictions) == 0:
            status = ClaimStatus.ACTIVE
        elif len(contradictions) > 0 and top_prob < self.theta_retract:
            status = ClaimStatus.RETRACTED
        elif len(contradictions) > 0:
            status = ClaimStatus.CONTESTED
        elif top_prob >= self.theta_provisional:
            status = ClaimStatus.PROVISIONAL

        claim_id = current_claim.claim_id if current_claim else f"claim_{top_cause}"
        learner_id = history[-1].learner_id if history else "anonymous"

        return LearnerClaim(
            claim_id=claim_id,
            learner_id=learner_id,
            skill_tag=history[-1].item_id if history else "general",
            claim_type=top_cause,
            status=status,
            confidence=round(top_prob, 3),
            supporting_events=list(set(supporting_event_ids)),
            contradicting_events=contradictions,
        )
