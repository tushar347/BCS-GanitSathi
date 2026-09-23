"""Comprehensive unit tests for Task 2.2 SymbolicVerifier.

Validates Section 5.2 of the GonitSathi Guideline:
- AST sandboxing preventing code execution attacks.
- Exact and alternative valid strategies.
- Known diagnostic error pattern localization.
- Bengali numeral and bilingual alias parsing.
- Arithmetic consistency and relation violation.
- Relational inequality verification (<=, >=, <, >).
- Proportional symbolic equivalence without constant false positives.
"""

import pytest
from src.verifier.symbolic_verifier import (
    SymbolicVerifier,
    ProblemReferenceDAG,
    ReferenceStep,
)
from src.controller.schemas import MathematicalStatus, InterpretationStatus


@pytest.fixture
def sample_problem_dag():
    return ProblemReferenceDAG(
        item_id="pct_012",
        family_id="inverse_budget_03",
        problem_text="চালের মূল্য ২৫% বৃদ্ধি পেলে ব্যবহার শতকরা কত কমাতে হবে?",
        declared_variables={
            "new_quantity": "Quantity after price increase",
            "new_price": "Price after increase",
            "decrease": "Percentage reduction in consumption",
        },
        variable_aliases={
            "new_quantity": ["নতুন পরিমাণ", "নতুন_পরিমাণ", "পরিমাণ"],
            "new_price": ["নতুন দাম", "নতুন_দাম", "দাম", "নতুন মূল্য"],
            "decrease": ["হ্রাস", "কমানো"],
        },
        reference_steps=[
            ReferenceStep(
                step_id="step_1",
                description="New price after 25% increase",
                target_variable="new_price",
                symbolic_expression="new_price = 100 * (1 + 0.25)",
                alternative_forms=["new_price = 125"],
            ),
            ReferenceStep(
                step_id="step_2",
                description="New quantity to keep budget 10000 constant",
                target_variable="new_quantity",
                symbolic_expression="new_quantity = 10000 / 125",
                alternative_forms=["new_quantity = 80"],
                known_error_patterns={
                    "new_quantity = 100 - 25": "fixed_budget_relation_violated_percentage_base_error",
                    "new_quantity = 75": "fixed_budget_relation_violated_percentage_base_error",
                },
            ),
        ],
    )


def test_ast_safety_guard():
    verifier = SymbolicVerifier()
    malicious_inputs = [
        "__import__('os').system('echo hacked')",
        "eval('1 + 1')",
        "exec('x = 5')",
        "open('/etc/passwd').read()",
        "[x for x in ().__class__.__base__.__subclasses__()]",
    ]
    for bad_input in malicious_inputs:
        res = verifier.verify_step(bad_input)
        assert res.mathematical_status == MathematicalStatus.UNVERIFIABLE
        assert "unsafe_ast" in res.verification_reason


def test_empty_or_whitespace_input():
    verifier = SymbolicVerifier()
    res = verifier.verify_step("   \n\t  ")
    assert res.mathematical_status == MathematicalStatus.UNVERIFIABLE
    assert res.verification_reason == "empty_or_whitespace_expression"


def test_valid_reference_step(sample_problem_dag):
    verifier = SymbolicVerifier()
    res = verifier.verify_step("new_quantity = 80", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.interpretation_status == InterpretationStatus.SUPPORTED
    assert res.matched_reference_step_id == "step_2"


def test_valid_bilingual_step_with_bengali_numerals_and_aliases(sample_problem_dag):
    verifier = SymbolicVerifier()
    # Bengali numerals '৮০' and alias 'নতুন পরিমাণ'
    res = verifier.verify_step("নতুন পরিমাণ = ৮০", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.VALID
    assert res.interpretation_status == InterpretationStatus.SUPPORTED
    assert res.matched_reference_step_id == "step_2"


def test_known_error_pattern(sample_problem_dag):
    verifier = SymbolicVerifier()
    # Student incorrectly calculates new quantity as 100 - 25
    res = verifier.verify_step("new_quantity = 100 - 25", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.interpretation_status == InterpretationStatus.SUPPORTED
    assert "percentage_base_error" in res.verification_reason


def test_known_error_pattern_bengali_input(sample_problem_dag):
    verifier = SymbolicVerifier()
    # Student writes in Bengali: 'নতুন_পরিমাণ = ১০০ - ২৫'
    res = verifier.verify_step("নতুন_পরিমাণ = ১০০ - ২৫", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert res.interpretation_status == InterpretationStatus.SUPPORTED
    assert "percentage_base_error" in res.verification_reason


def test_valid_alternative_strategy(sample_problem_dag):
    verifier = SymbolicVerifier()
    # Equivalent valid formulation: new_quantity = 10000 / 125
    res = verifier.verify_step("new_quantity = 10000 / 125", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.VALID


def test_undeclared_variables_yield_unsupported(sample_problem_dag):
    verifier = SymbolicVerifier()
    # 'foreign_variable' is not in declared_variables
    res = verifier.verify_step("foreign_variable = 100", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.UNSUPPORTED
    assert "undeclared_variables" in res.verification_reason


def test_relation_violated_arithmetic(sample_problem_dag):
    verifier = SymbolicVerifier()
    # Arithmetic contradiction on declared variable: new_quantity = 95 != 80
    res = verifier.verify_step("new_quantity = 95", sample_problem_dag)
    assert res.mathematical_status == MathematicalStatus.INVALID
    assert "relation_violated" in res.verification_reason


def test_standalone_verification_without_dag():
    verifier = SymbolicVerifier()
    # Pure identity
    res1 = verifier.verify_step("100 - 25 = 75")
    assert res1.mathematical_status == MathematicalStatus.VALID

    # Arithmetic false
    res2 = verifier.verify_step("100 - 25 = 80")
    assert res2.mathematical_status == MathematicalStatus.INVALID

    # Pure expression
    res3 = verifier.verify_step("125 + 50")
    assert res3.mathematical_status == MathematicalStatus.VALID


def test_inequality_verification():
    verifier = SymbolicVerifier()
    # Standalone inequalities with constants
    res1 = verifier.verify_step("5 <= 10")
    assert res1.mathematical_status == MathematicalStatus.VALID

    res2 = verifier.verify_step("15 <= 10")
    assert res2.mathematical_status == MathematicalStatus.INVALID

    # Symbolic inequality equivalence check
    assert verifier._check_equivalence("x <= 10", "2*x <= 20")
    assert verifier._check_equivalence("x <= 10", "-x >= -10")
    assert not verifier._check_equivalence("x <= 10", "x >= 10")


def test_proportional_equivalence_does_not_conflate_constants():
    verifier = SymbolicVerifier()
    # Equations with variables should allow positive scalar scaling
    assert verifier._check_equivalence("x = 5", "2*x = 10")

    # Pure constant equations must NOT be treated as proportionally equivalent
    assert not verifier._check_equivalence("10 = 5", "20 = 5")
