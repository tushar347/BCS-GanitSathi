"""Tests for Baseline B0: Reviewed Rule / Template Tutor."""

import pytest
from src.baselines.b0_rule_template import RuleTemplateTutor
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


def test_b0_empty_input_clarification(sample_dag):
    tutor = RuleTemplateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("?", sample_dag)
    assert res.action.action_type == ActionType.ASK_CLARIFICATION
    assert res.mathematical_status == MathematicalStatus.UNVERIFIABLE


def test_b0_known_error_pattern(sample_dag):
    tutor = RuleTemplateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("আমার মনে হয় answer = 11", sample_dag)
    assert res.action.action_type == ActionType.GIVE_CONCEPTUAL_HINT
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.is_first_error is True
    assert res.first_error_reason == "M_PRIME_COUNT_conceptual"
    assert res.predicted_cause == CandidateCause.PERCENTAGE_BASE


def test_b0_correct_step(sample_dag):
    tutor = RuleTemplateTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 10", sample_dag)
    assert res.action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.predicted_cause == CandidateCause.NO_ERROR
