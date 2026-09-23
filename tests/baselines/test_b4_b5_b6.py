"""Tests for Baselines B4, B5, B6."""

import pytest
from src.baselines.b4_intellicode import IntelliCodeTutor
from src.baselines.b5_scaffoldlm import ScaffoldLMTutor
from src.baselines.b6_slow import SlowWorkspaceTutor
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
                target_variable="intermediate_1",
                symbolic_expression="intermediate_1 = 10",
                known_error_patterns={"intermediate_1 = 11": "M_PRIME_COUNT_conceptual"},
            ),
            ReferenceStep(
                step_id="step_2",
                description="চূড়ান্ত উত্তর নির্ধারণ",
                target_variable="answer",
                symbolic_expression="answer = 10",
                known_error_patterns={},
            ),
        ],
    )


# ---------- B4 IntelliCode Tests ----------

def test_b4_correct_step_increases_mastery(sample_dag):
    tutor = IntelliCodeTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("intermediate_1 = 10", sample_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP
    assert tutor.bkt_state.p_mastery > 0.30


def test_b4_repeated_error_graduated_hint(sample_dag):
    tutor = IntelliCodeTutor()
    tutor.reset("learner_1", sample_dag)
    res1 = tutor.process_student_step("intermediate_1 = 11", sample_dag)
    assert res1.action.action_type == ActionType.GIVE_CONCEPTUAL_HINT

    res2 = tutor.process_student_step("intermediate_1 = 11", sample_dag)
    assert res2.action.action_type == ActionType.OFFER_LOCAL_SCAFFOLD
    assert len(res2.active_commitments) > 0


# ---------- B5 ScaffoldLM Tests ----------

def test_b5_plan_progression(sample_dag):
    tutor = ScaffoldLMTutor()
    tutor.reset("learner_1", sample_dag)
    res1 = tutor.process_student_step("intermediate_1 = 10", sample_dag)
    assert res1.mathematical_status == MathematicalStatus.VALID
    assert tutor.current_step_index == 1
    assert "পরবর্তী ধাপ 2" in res1.action.payload


def test_b5_step_remediation_on_error(sample_dag):
    tutor = ScaffoldLMTutor()
    tutor.reset("learner_1", sample_dag)
    res = tutor.process_student_step("intermediate_1 = 11", sample_dag)
    assert res.action.action_type == ActionType.OFFER_LOCAL_SCAFFOLD
    assert "পরিকল্পনার ধাপ 1 সম্পন্ন করতে" in res.action.payload
    assert len(res.active_commitments) > 0


# ---------- B6 SLOW Tests ----------

def test_b6_counterfactual_simulation(sample_dag):
    tutor = SlowWorkspaceTutor()
    tutor.reset("learner_1", sample_dag)
    # Step has target 10; student gives 11 (delta=1.0)
    # B6 counterfactual workspace shifts conceptual error to transient slip
    res = tutor.process_student_step("intermediate_1 = 11", sample_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.predicted_cause == CandidateCause.TRANSIENT_SLIP
    assert res.neural_calls == 1
    assert res.symbolic_calls == 2
    assert len(tutor.diagnostic_workspace) == 1
