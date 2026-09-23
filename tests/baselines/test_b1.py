"""Tests for Baseline B1: Strong Prompted Tutor."""

import pytest
from src.baselines.b1_prompted import PromptedTutor
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


def test_b1_offline_simulation_valid(sample_dag):
    tutor = PromptedTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("উত্তর ১০", sample_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP
    assert res.predicted_cause == CandidateCause.NO_ERROR
    assert res.neural_calls == 0


def test_b1_offline_simulation_error_premature_commitment(sample_dag):
    tutor = PromptedTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("answer = 11", sample_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.action.action_type == ActionType.GIVE_CONCEPTUAL_HINT
    # Prompted baseline immediately commits on turn 1 (key failure mode documented in §8)
    assert len(res.active_commitments) == 1
    assert res.active_commitments[0]["cause"] == CandidateCause.PERCENTAGE_BASE.value


def test_b1_injected_llm_callable(sample_dag):
    mock_json = '{"interpreted_math": "10", "mathematical_status": "valid", "diagnosis": "no_error", "action_type": "acknowledge_correct_step", "response_bn": "খুব ভালো!"}'
    tutor = PromptedTutor(llm_callable=lambda prompt: mock_json)
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("আমার উত্তর ১০", sample_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.action.payload == "খুব ভালো!"
    assert res.neural_calls == 1
