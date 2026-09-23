"""Tests for Baseline B2: Verify-Then-Generate Tutor."""

import pytest
from src.baselines.b2_verify_then_generate import VerifyThenGenerateTutor
from src.controller.schemas import ActionType, CandidateCause, MathematicalStatus
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep


@pytest.fixture
def sample_dag():
    return ProblemReferenceDAG(
        item_id="BCS10_Q085",
        family_id="prime_numbers_in_range_f01",
        problem_text="১ থেকে ৩০ পর্যন্ত কয়টি মৌলিক সংখ্যা আছে?",
        declared_variables={"answer": "10"},
        reference_steps=[
            ReferenceStep(
                step_id="step_1",
                description="মৌলিক সংখ্যার তালিকা তৈরি",
                target_variable="answer",
                symbolic_expression="answer = 10",
                known_error_patterns={"answer = 11": "M_PRIME_COUNT_conceptual"},
            )
        ],
    )


def test_b2_valid_step_verification(sample_dag):
    tutor = VerifyThenGenerateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 10", sample_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP
    assert res.predicted_cause == CandidateCause.NO_ERROR
    assert res.symbolic_calls == 1
    assert res.neural_calls == 0


def test_b2_invalid_step_verification(sample_dag):
    tutor = VerifyThenGenerateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 11", sample_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.action.action_type == ActionType.GIVE_CONCEPTUAL_HINT
    assert res.is_first_error is True
    assert res.predicted_cause == CandidateCause.PERCENTAGE_BASE
    assert res.symbolic_calls == 1


def test_b2_no_persistent_commitments(sample_dag):
    tutor = VerifyThenGenerateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 11", sample_dag)
    # B2 MUST NOT have persistent active commitments (the key ablation difference vs G)
    assert res.active_commitments == []
