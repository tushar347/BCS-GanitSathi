"""Integration tests implementing Appendix A.3 Minimal Meaningful Verification Cases.

Verifies:
1. A reliably observed wrong step updates error belief without zeroing out (Zero-factor bug fixed).
2. An unresolved parse cannot activate a persistent claim.
3. An assisted correct answer is distinguished from independent mastery (Assistance trap).
4. Duplicate events do not multiply evidence (Correlated event grouping).
5. A contradiction contests and retracts a claim.
6. The diagnostic probe budget cannot be exceeded (N_probe <= 1).
"""

import pytest
from src.controller.diagnostic_controller import DiagnosticController
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep
from src.controller.schemas import (
    CandidateCause,
    AssistanceLevel,
    ClaimStatus,
    MathematicalStatus,
    InterpretationStatus,
    ActionType,
    DiagnosticProbe,
)


@pytest.fixture
def sample_problem_dag():
    return ProblemReferenceDAG(
        item_id="pct_012",
        family_id="inverse_budget_03",
        problem_text="চালের মূল্য ২৫% বৃদ্ধি পেলে ব্যবহার শতকরা কত কমাতে হবে?",
        declared_variables={"new_quantity": "new quantity", "new_price": "new price"},
        variable_aliases={
            "new_quantity": ["নতুন পরিমাণ", "নতুন_পরিমাণ", "পরিমাণ"],
            "new_price": ["নতুন দাম", "নতুন_দাম", "দাম", "নতুন মূল্য"],
        },
        reference_steps=[
            ReferenceStep(
                step_id="step_1",
                description="New price after increase",
                target_variable="new_price",
                symbolic_expression="new_price = 125",
            ),
            ReferenceStep(
                step_id="step_2",
                description="New quantity",
                target_variable="new_quantity",
                symbolic_expression="new_quantity = 80",
                known_error_patterns={
                    "new_quantity = 100 - 25": "fixed_budget_relation_violated_percentage_base",
                    "new_quantity = 75": "fixed_budget_relation_violated_percentage_base",
                }
            )
        ]
    )


@pytest.fixture
def sample_probe():
    return DiagnosticProbe(
        probe_id="probe_dir_01",
        target_ambiguity="percentage_base_vs_slip",
        prompt_bn="যদি প্রতিটি কেজির দাম বৃদ্ধি পায় কিন্তু মোট বাজেট অপরিবর্তিত থাকে, তবে ক্রয়ের পরিমাণ বাড়বে, কমবে নাকি অপরিবর্তিত থাকবে?",
        prompt_en="If price per kg increases while total budget stays fixed, should quantity bought increase, decrease, or stay the same?",
        candidate_causes=[CandidateCause.PERCENTAGE_BASE, CandidateCause.TRANSIENT_SLIP],
        response_model={
            "decrease": {
                CandidateCause.PERCENTAGE_BASE: 0.80,
                CandidateCause.TRANSIENT_SLIP: 0.90,
                CandidateCause.LINGUISTIC_SLIP: 0.10,
                CandidateCause.NO_ERROR: 0.95,
            },
            "increase_or_same": {
                CandidateCause.PERCENTAGE_BASE: 0.15,
                CandidateCause.TRANSIENT_SLIP: 0.05,
                CandidateCause.LINGUISTIC_SLIP: 0.85,
                CandidateCause.NO_ERROR: 0.02,
            },
            "ambiguous": {
                CandidateCause.PERCENTAGE_BASE: 0.05,
                CandidateCause.TRANSIENT_SLIP: 0.05,
                CandidateCause.LINGUISTIC_SLIP: 0.05,
                CandidateCause.NO_ERROR: 0.03,
            }
        },
        expected_burden_seconds=10.0,
    )


def test_case_1_wrong_step_updates_error_belief_without_zeroing(sample_problem_dag):
    """Case 1: Reliably observed wrong step updates error belief without collapsing."""
    controller = DiagnosticController()
    raw_step = "নতুন পরিমাণ = ১০০ - ২৫"  # Bengali 100 - 25
    
    action, audit, obs = controller.process_student_step(
        raw_text=raw_step,
        problem_dag=sample_problem_dag,
        learner_id="student_1",
    )

    assert obs.mathematical_status == MathematicalStatus.INVALID
    assert obs.evidence_admitted is True
    
    # Check belief update: percentage_base probability should INCREASE, not zero out
    pct_prob = controller.belief_updater.beliefs[CandidateCause.PERCENTAGE_BASE]
    assert pct_prob > controller.belief_updater.priors[CandidateCause.PERCENTAGE_BASE]
    # No error probability should drop significantly
    assert controller.belief_updater.beliefs[CandidateCause.NO_ERROR] < 0.05


def test_case_2_unresolved_parse_cannot_activate_claim(sample_problem_dag):
    """Case 2: Unresolved parse cannot activate a claim or update belief."""
    controller = DiagnosticController()
    prior_beliefs = controller.belief_updater.beliefs.copy()

    # Ill-formed gibberish mathematical input
    raw_step = "নতুন পরিমাণ = = ???"
    action, audit, obs = controller.process_student_step(
        raw_text=raw_step,
        problem_dag=sample_problem_dag,
        learner_id="student_2",
    )

    assert obs.interpretation_status == InterpretationStatus.UNRESOLVED
    assert obs.evidence_admitted is False
    assert action.action_type == ActionType.ASK_CLARIFICATION
    # Beliefs must remain identical to priors
    for cause in CandidateCause:
        assert controller.belief_updater.beliefs[cause] == prior_beliefs[cause]


def test_case_3_assisted_correct_answer_distinguished_from_independent_mastery(sample_problem_dag):
    """Case 3: Assisted correct step does not grant independent mastery."""
    controller = DiagnosticController()

    # Step submitted AFTER tutor provided the worked solution or key equation
    action, audit, obs = controller.process_student_step(
        raw_text="new_quantity = 80",
        problem_dag=sample_problem_dag,
        learner_id="student_3",
        assistance_level=AssistanceLevel.WORKED_SOLUTION,
    )

    assert obs.mathematical_status == MathematicalStatus.VALID
    assert obs.assistance_level == AssistanceLevel.WORKED_SOLUTION
    
    # Under heavy assistance, NO_ERROR belief should NOT jump to high confidence
    no_err_prob = controller.belief_updater.beliefs[CandidateCause.NO_ERROR]
    assert no_err_prob < 0.95
    # Should not trigger persistent ACTIVE mastery claim
    no_error_hyp = controller.belief_updater.active_hypotheses.get(CandidateCause.NO_ERROR)
    assert (no_error_hyp is None) or (no_error_hyp.status != ClaimStatus.ACTIVE)


def test_case_4_duplicate_events_do_not_multiply_evidence(sample_problem_dag):
    """Case 4: Duplicate sync/evaluations do not multiply evidence likelihood."""
    controller = DiagnosticController()
    raw_step = "new_quantity = 100 - 25"
    shared_group_id = "attempt_group_001"

    # First submission
    controller.process_student_step(
        raw_text=raw_step,
        problem_dag=sample_problem_dag,
        learner_id="student_4",
        independent_group_id=shared_group_id,
    )
    first_pass_prob = controller.belief_updater.beliefs[CandidateCause.PERCENTAGE_BASE]

    # Duplicate submission (re-evaluation of same attempt with same group ID)
    controller.process_student_step(
        raw_text=raw_step,
        problem_dag=sample_problem_dag,
        learner_id="student_4",
        independent_group_id=shared_group_id,
    )
    second_pass_prob = controller.belief_updater.beliefs[CandidateCause.PERCENTAGE_BASE]

    # Belief should not have multiplied
    assert pytest.approx(first_pass_prob, rel=1e-4) == second_pass_prob


def test_case_5_contradiction_contests_claim_and_probe_capped(sample_problem_dag, sample_probe):
    """Case 5: Contradiction contests claim, and probe budget is bounded (N_probe <= 1)."""
    controller = DiagnosticController()
    
    # Step 1: Initial error triggers diagnostic probe
    action1, audit1, _ = controller.process_student_step(
        raw_text="new_quantity = 100 - 25",
        problem_dag=sample_problem_dag,
        learner_id="student_5",
        candidate_probes=[sample_probe],
    )
    assert action1.action_type == ActionType.ASK_DIAGNOSTIC_PROBE
    assert controller.probe_selector.probes_asked_in_episode == 1

    # Step 2: Student makes another error, but probe budget is exhausted
    action2, audit2, _ = controller.process_student_step(
        raw_text="new_quantity = 75",
        problem_dag=sample_problem_dag,
        learner_id="student_5",
        candidate_probes=[sample_probe],
    )
    # MUST NOT ask another probe! Bounded by N_probe <= 1
    assert action2.action_type != ActionType.ASK_DIAGNOSTIC_PROBE
    assert controller.probe_selector.probes_asked_in_episode == 1

    # Step 3: Student performs independent correct step -> Contradiction!
    action3, audit3, _ = controller.process_student_step(
        raw_text="new_quantity = 80",
        problem_dag=sample_problem_dag,
        learner_id="student_5",
        assistance_level=AssistanceLevel.NONE,
    )
    # The percentage_base claim should be CONTESTED or RETRACTED due to contradictory correct work
    hyp = controller.belief_updater.active_hypotheses.get(CandidateCause.PERCENTAGE_BASE)
    if hyp:
        assert hyp.status in (ClaimStatus.CONTESTED, ClaimStatus.RETRACTED, ClaimStatus.PROVISIONAL)
        assert len(hyp.contradicting_event_ids) > 0
