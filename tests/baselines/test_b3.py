"""Tests for Baseline B3: Bayesian Diagnostic Tutor."""

import pytest
from src.baselines.b3_bayesian import BayesianDiagnosticTutor
from src.controller.schemas import CandidateCause, MathematicalStatus
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


def test_b3_correct_step_shifts_belief(sample_dag):
    tutor = BayesianDiagnosticTutor(activation_threshold=0.75)
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 10", sample_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.beliefs[CandidateCause.NO_ERROR] > 0.40
    assert res.predicted_cause == CandidateCause.NO_ERROR
    assert res.symbolic_calls == 1


def test_b3_invalid_step_shifts_belief(sample_dag):
    tutor = BayesianDiagnosticTutor(activation_threshold=0.75)
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 11", sample_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.beliefs[CandidateCause.PERCENTAGE_BASE] > 0.40
    assert res.is_first_error is True


def test_b3_repeated_errors_activate_commitment(sample_dag):
    tutor = BayesianDiagnosticTutor(activation_threshold=0.60)
    tutor.reset("learner_1", sample_dag)
    tutor.process_student_step("answer = 11", sample_dag)
    res2 = tutor.process_student_step("answer = 11", sample_dag)
    assert len(res2.active_commitments) > 0
    assert res2.active_commitments[0]["cause"] == CandidateCause.PERCENTAGE_BASE.value
