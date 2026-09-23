"""Dedicated unit test suite validating Task 2.3 & Task 2.4 implementations.

Audited and validated by RA4 (Evaluation Lead).
Covers:
- Task 2.3: Evidence Admission, assistance tagging, independent grouping, de-duplication.
- Task 2.4: Categorical belief model over candidate causes, Laplace smoothing, claim governance.
"""

import pytest
from src.controller.evidence_admission import EvidenceAdmissionManager
from src.controller.belief_updater import CalibratedBeliefUpdater
from src.controller.schemas import (
    Observation,
    InterpretationStatus,
    MathematicalStatus,
    AssistanceLevel,
    CandidateCause,
    ClaimStatus,
)


class TestTask23EvidenceAdmission:
    """Audit of Task 2.3 (EvidenceAdmissionManager)."""

    def test_admit_valid_mathematical_step(self):
        manager = EvidenceAdmissionManager()
        obs = Observation(
            event_id="ev_001",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_1",
            original_text="x = 5",
            normalized_text="x = 5",
            mathematical_status=MathematicalStatus.VALID,
        )
        admitted, reason = manager.evaluate_admission(obs)
        assert admitted is True
        assert "valid_step_admitted" in reason

        processed = manager.record_and_admit(obs)
        assert processed.evidence_admitted is True
        assert manager.is_first_in_evidence_group(processed) is True

    def test_admit_invalid_step_zero_factor_fix(self):
        """Invalid mathematical step is high-confidence evidence of error."""
        manager = EvidenceAdmissionManager()
        obs = Observation(
            event_id="ev_002",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_1",
            original_text="x = 10",
            normalized_text="x = 10",
            mathematical_status=MathematicalStatus.INVALID,
        )
        admitted, reason = manager.evaluate_admission(obs)
        assert admitted is True
        assert "valid_evidence_of_mathematical_error" in reason

    def test_reject_unresolved_interpretation(self):
        """Unresolved parse cannot be admitted into diagnostic belief updating."""
        manager = EvidenceAdmissionManager()
        obs = Observation(
            event_id="ev_003",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_1",
            original_text="???",
            normalized_text="???",
            interpretation_status=InterpretationStatus.UNRESOLVED,
            mathematical_status=MathematicalStatus.UNVERIFIABLE,
        )
        admitted, reason = manager.evaluate_admission(obs)
        assert admitted is False
        assert "unresolved_interpretation" in reason

    def test_deduplicate_identical_event_id(self):
        """Duplicate raw event IDs must be rejected."""
        manager = EvidenceAdmissionManager()
        obs = Observation(
            event_id="ev_dup_1",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_1",
            original_text="x = 5",
            normalized_text="x = 5",
            mathematical_status=MathematicalStatus.VALID,
        )
        manager.record_and_admit(obs)
        admitted, reason = manager.evaluate_admission(obs)
        assert admitted is False
        assert reason == "duplicate_event_id"

    def test_independent_evidence_group_tracking(self):
        manager = EvidenceAdmissionManager()
        obs1 = Observation(
            event_id="ev_grp_1",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_alpha",
            original_text="x = 1",
            normalized_text="x = 1",
            mathematical_status=MathematicalStatus.INVALID,
        )
        obs2 = Observation(
            event_id="ev_grp_2",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_alpha",  # Same group
            original_text="x = 2",
            normalized_text="x = 2",
            mathematical_status=MathematicalStatus.INVALID,
        )
        manager.record_and_admit(obs1)
        manager.record_and_admit(obs2)

        assert manager.is_first_in_evidence_group(obs1) is True
        assert manager.is_first_in_evidence_group(obs2) is False
        assert manager.get_independent_evidence_count() == 1


class TestTask24BeliefUpdater:
    """Audit of Task 2.4 (CalibratedBeliefUpdater)."""

    def test_priors_and_entropy(self):
        updater = CalibratedBeliefUpdater()
        assert sum(updater.beliefs.values()) == pytest.approx(1.0, abs=1e-5)
        ent = updater.get_shannon_entropy()
        assert ent > 2.0  # Distributed across causes

    def test_unassisted_invalid_step_updates_beliefs_without_zero_mass(self):
        updater = CalibratedBeliefUpdater()
        prior_pct = updater.beliefs[CandidateCause.PERCENTAGE_BASE]

        obs = Observation(
            event_id="ev_err_1",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_1",
            original_text="ans = 75",
            normalized_text="ans = 75",
            mathematical_status=MathematicalStatus.INVALID,
            candidate_causes=[CandidateCause.PERCENTAGE_BASE],
            assistance_level=AssistanceLevel.NONE,
            evidence_admitted=True,
        )
        new_beliefs = updater.update_with_observation(obs, is_first_in_group=True)

        assert new_beliefs[CandidateCause.PERCENTAGE_BASE] > prior_pct
        assert new_beliefs[CandidateCause.NO_ERROR] < 0.05
        assert all(prob >= 0.0 for prob in new_beliefs.values())
        assert sum(new_beliefs.values()) == pytest.approx(1.0, abs=1e-5)

    def test_two_observation_rule_for_claim_activation(self):
        """Active claim requires posterior >= theta_commit AND >= 2 independent evidence groups."""
        updater = CalibratedBeliefUpdater(activation_threshold=0.80)

        # Observation 1 from group 1
        obs1 = Observation(
            event_id="ev_obs_1",
            learner_id="student_1",
            item_id="item_01",
            family_id="fam_01",
            independent_evidence_group="grp_independent_1",
            original_text="ans = 75",
            normalized_text="ans = 75",
            mathematical_status=MathematicalStatus.INVALID,
            candidate_causes=[CandidateCause.PERCENTAGE_BASE],
            evidence_admitted=True,
        )
        updater.update_with_observation(obs1, is_first_in_group=True)
        hyp = updater.active_hypotheses[CandidateCause.PERCENTAGE_BASE]
        # Even if posterior is high, 1 group cannot activate claim
        assert hyp.status == ClaimStatus.PROVISIONAL

        # Observation 2 from group 2 (independent)
        obs2 = Observation(
            event_id="ev_obs_2",
            learner_id="student_1",
            item_id="item_02",
            family_id="fam_01",
            independent_evidence_group="grp_independent_2",
            original_text="ans = 75",
            normalized_text="ans = 75",
            mathematical_status=MathematicalStatus.INVALID,
            candidate_causes=[CandidateCause.PERCENTAGE_BASE],
            evidence_admitted=True,
        )
        updater.update_with_observation(obs2, is_first_in_group=True)
        hyp = updater.active_hypotheses[CandidateCause.PERCENTAGE_BASE]

        assert hyp.probability >= 0.80
        assert hyp.status == ClaimStatus.ACTIVE

    def test_claim_contestation_on_contradiction(self):
        """Valid independent step contests active error claim."""
        updater = CalibratedBeliefUpdater(activation_threshold=0.80)

        # Establish active claim with 2 independent groups
        for i, grp in enumerate(["grp_A", "grp_B"]):
            obs = Observation(
                event_id=f"ev_init_{i}",
                learner_id="student_1",
                item_id="item_01",
                family_id="fam_01",
                independent_evidence_group=grp,
                original_text="ans = 75",
                normalized_text="ans = 75",
                mathematical_status=MathematicalStatus.INVALID,
                candidate_causes=[CandidateCause.PERCENTAGE_BASE],
                evidence_admitted=True,
            )
            updater.update_with_observation(obs, is_first_in_group=True)

        hyp = updater.active_hypotheses[CandidateCause.PERCENTAGE_BASE]
        assert hyp.status == ClaimStatus.ACTIVE

        # Independent valid step
        contradicting_obs = Observation(
            event_id="ev_valid_corr",
            learner_id="student_1",
            item_id="item_03",
            family_id="fam_01",
            independent_evidence_group="grp_C",
            original_text="ans = 80",
            normalized_text="ans = 80",
            mathematical_status=MathematicalStatus.VALID,
            assistance_level=AssistanceLevel.NONE,
            evidence_admitted=True,
        )
        updater.update_with_observation(contradicting_obs, is_first_in_group=True)

        # Must be contested!
        assert hyp.status in (ClaimStatus.CONTESTED, ClaimStatus.RETRACTED)
        assert "ev_valid_corr" in hyp.contradicting_event_ids
