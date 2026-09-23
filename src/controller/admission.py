from typing import List
from src.controller.schemas import (
    AssistanceLevel,
    InterpretationStatus,
    MathematicalStatus,
    Observation,
)


class EvidenceAdmissionPolicy:
    """
    Evidence Admission Controller (§5.3):
    Governs whether an observed student event is admitted as diagnostic evidence.
    Enforces de-duplication, assistance weighting, and error-integrity.
    """

    ASSISTANCE_WEIGHTS = {
        AssistanceLevel.NONE: 1.0,
        AssistanceLevel.CONCEPTUAL_HINT: 0.5,
        AssistanceLevel.KEY_EQUATION_SUPPLIED: 0.2,
        AssistanceLevel.WORKED_SOLUTION: 0.0,
    }

    @classmethod
    def evaluate_admission(
        cls,
        record: Observation,
        history: List[Observation],
    ) -> bool:
        # Rule 1 (§5.2): Unresolved or unparsed interpretations cannot update diagnostic belief
        if record.interpretation_status == InterpretationStatus.UNRESOLVED:
            return False

        # Rule 2 (§5.3): Duplicate event suppression
        # If an event with the same independent_evidence_group and normalized text already exists, reject
        for prior in history:
            if (
                prior.independent_evidence_group == record.independent_evidence_group
                and prior.normalized_text == record.normalized_text
                and prior.item_id == record.item_id
            ):
                return False

        # Rule 3 (§2.2 Integrity Guard):
        # Reliably verified wrong steps ARE admissible diagnostic evidence
        if (
            record.mathematical_status == MathematicalStatus.INVALID
            and record.interpretation_status == InterpretationStatus.SUPPORTED
        ):
            return True

        # Rule 4: Valid steps are admitted
        if record.mathematical_status == MathematicalStatus.VALID:
            return True

        return True

    @classmethod
    def get_assistance_discount(cls, level: AssistanceLevel) -> float:
        """Returns the evidentiary weight discount based on assistance received (§5.3)."""
        return cls.ASSISTANCE_WEIGHTS.get(level, 1.0)
