"""Shared pytest fixtures for GonitSathi test suite.

Provides reusable fixtures for:
- Problem DAGs (reference solution graphs)
- Diagnostic probes
- Controller instances with pre-configured thresholds
- Benchmark-style attempt histories
- Bengali text samples for normalizer testing
"""

import pytest
from src.controller.diagnostic_controller import DiagnosticController
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep
from src.normalizer.bengali_normalizer import BengaliNormalizer
from src.controller.schemas import (
    CandidateCause,
    DiagnosticProbe,
)


# ---------------------------------------------------------------------------
# Problem DAG Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def percentage_problem_dag():
    """Standard percentage/budget inverse problem (§7.2 family: inverse_budget).

    Reference answer: new_price = 125, new_quantity = 80.
    Known error pattern: student computes 100 - 25 = 75 (percentage_base error).
    """
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
                },
            ),
        ],
    )


@pytest.fixture
def simple_arithmetic_dag():
    """Simple two-step arithmetic problem for basic verifier testing."""
    return ProblemReferenceDAG(
        item_id="arith_001",
        family_id="basic_addition_01",
        problem_text="যদি ক = ১৫ এবং খ = ২৫ হয়, তবে ক + খ = ?",
        declared_variables={"a": "ক", "b": "খ", "result": "ফলাফল"},
        variable_aliases={
            "a": ["ক"],
            "b": ["খ"],
            "result": ["ফলাফল", "উত্তর"],
        },
        reference_steps=[
            ReferenceStep(
                step_id="step_1",
                description="Sum",
                target_variable="result",
                symbolic_expression="result = 15 + 25",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Diagnostic Probe Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def percentage_base_probe():
    """Diagnostic probe targeting percentage_base vs transient_slip ambiguity."""
    return DiagnosticProbe(
        probe_id="probe_dir_01",
        target_ambiguity="percentage_base_vs_slip",
        prompt_bn="যদি প্রতিটি কেজির দাম বৃদ্ধি পায় কিন্তু মোট বাজেট অপরিবর্তিত থাকে, তবে ক্রয়ের পরিমাণ বাড়বে, কমবে নাকি অপরিবর্তিত থাকবে?",
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
            },
        },
        expected_burden_seconds=10.0,
    )


# ---------------------------------------------------------------------------
# Controller Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_controller():
    """A fresh DiagnosticController with default thresholds."""
    return DiagnosticController()


@pytest.fixture
def strict_controller():
    """A DiagnosticController with high activation threshold (0.95) for strict testing."""
    return DiagnosticController(activation_threshold=0.95, entropy_threshold=0.4)


@pytest.fixture
def lenient_controller():
    """A DiagnosticController with low activation threshold (0.70) for coverage testing."""
    return DiagnosticController(activation_threshold=0.70, entropy_threshold=0.8)


# ---------------------------------------------------------------------------
# Normalizer Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def normalizer():
    """A fresh BengaliNormalizer instance."""
    return BengaliNormalizer()


# ---------------------------------------------------------------------------
# Bengali Text Samples
# ---------------------------------------------------------------------------

@pytest.fixture
def bengali_error_step():
    """Bengali text for a known percentage_base error: 'new_quantity = 100 - 25'."""
    return "নতুন পরিমাণ = ১০০ - ২৫"


@pytest.fixture
def bengali_correct_step():
    """Bengali text for the correct answer: 'new_quantity = 80'."""
    return "নতুন পরিমাণ = ৮০"


@pytest.fixture
def bengali_gibberish_step():
    """Ill-formed mathematical input that should trigger UNRESOLVED parse."""
    return "নতুন পরিমাণ = = ???"


# ---------------------------------------------------------------------------
# Attempt History Fixtures (for benchmark loader testing)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_attempt_history_correct():
    """A well-formed attempt history representing correct independent work."""
    return {
        "history_id": "hist_001",
        "history_type": "correct_work",
        "events": [
            {
                "text": "new_price = 125",
                "assistance_level": "none",
                "independent_evidence_group": "group_1",
            },
            {
                "text": "new_quantity = 80",
                "assistance_level": "none",
                "independent_evidence_group": "group_2",
            },
        ],
        "latent_cause": "no_error",
    }


@pytest.fixture
def sample_attempt_history_error():
    """A well-formed attempt history with a percentage_base error."""
    return {
        "history_id": "hist_002",
        "history_type": "conceptual_error",
        "events": [
            {
                "text": "new_price = 125",
                "assistance_level": "none",
                "independent_evidence_group": "group_1",
            },
            {
                "text": "new_quantity = 100 - 25",
                "assistance_level": "none",
                "independent_evidence_group": "group_2",
            },
        ],
        "latent_cause": "percentage_base",
    }


@pytest.fixture
def sample_benchmark_dataset():
    """Minimal valid benchmark dataset structure for loader validation."""
    return {
        "split": "dev",
        "families": [
            {
                "item_id": "pct_012",
                "family_id": "inverse_budget_03",
                "topic": "percentage",
                "difficulty": "medium",
                "question_bn": "চালের মূল্য ২৫% বৃদ্ধি পেলে ব্যবহার শতকরা কত কমাতে হবে?",
                "declared_variables": {"new_quantity": "new quantity", "new_price": "new price"},
                "reference_steps": [
                    {
                        "step_id": "step_1",
                        "symbolic_expression": "new_price = 125",
                    },
                    {
                        "step_id": "step_2",
                        "symbolic_expression": "new_quantity = 80",
                        "known_error_patterns": {
                            "new_quantity = 100 - 25": "percentage_base",
                        },
                    },
                ],
                "attempt_histories": [
                    {
                        "history_id": "hist_001",
                        "history_type": "correct_work",
                        "events": [
                            {
                                "text": "new_quantity = 80",
                                "assistance_level": "none",
                                "independent_evidence_group": "group_1",
                            },
                        ],
                    },
                ],
            },
        ],
    }
