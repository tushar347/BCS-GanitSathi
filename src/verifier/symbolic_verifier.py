"""Deterministic symbolic mathematical verifier using restricted AST and SymPy.

Conforms to Section 5.2 of GonitSathi Guideline:
- Restricted AST parsing (strictly forbids arbitrary Python execution/eval).
- Checks variable binding, assumptions, and symbolic equivalence.
- Distinguishes valid, invalid, unverifiable, and unsupported statuses.
- Recognizes alternative valid strategies.
- Fully supports equations and inequalities (<=, >=, <, >, ==, =).
- Integrates seamlessly with BengaliNormalizer for end-to-end bilingual verification.
"""

from __future__ import annotations
import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

from src.controller.schemas import (
    MathematicalStatus,
    InterpretationStatus,
    VerificationResult,
)
from src.normalizer.bengali_normalizer import BengaliNormalizer


# Whitelist safe AST nodes
ALLOWED_AST_NODES = (
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.Name,
    ast.Constant,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.FloorDiv,
    ast.Mod,
    ast.Compare,
    ast.Eq,
    ast.Lt,
    ast.Gt,
    ast.LtE,
    ast.GtE,
    ast.Load,
    ast.Store,
)


@dataclass
class ReferenceStep:
    step_id: str
    description: str
    target_variable: str
    # sympy relation or equation, e.g. "Q_new * P_new - Q_old * P_old" or "new_quantity - 80"
    symbolic_expression: str
    # Alternative valid expressions
    alternative_forms: List[str] = field(default_factory=list)
    # Expected known error patterns (for immediate diagnostic localization)
    known_error_patterns: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProblemReferenceDAG:
    item_id: str
    family_id: str
    problem_text: str
    declared_variables: Dict[str, str]  # e.g. {"new_quantity": "Quantity after price increase"}
    variable_aliases: Dict[str, List[str]] = field(default_factory=dict)
    reference_steps: List[ReferenceStep] = field(default_factory=list)
    boundary_constraints: List[str] = field(default_factory=list)
    accepted_answer_forms: List[str] = field(default_factory=list)


ALLOWED_CONSTANT_TYPES = (int, float, complex)


class SymbolicVerifier:
    """Verifies mathematical relations deterministically without executing unconstrained code."""

    def __init__(self, normalizer: Optional[BengaliNormalizer] = None):
        self.transformations = standard_transformations + (implicit_multiplication_application,)
        self.normalizer = normalizer or BengaliNormalizer()

    def _canonical_answer_text(self, text: str) -> str:
        normalized = self.normalizer.normalize(text).normalized_text.lower().strip()
        normalized = re.sub(r"^(?:final_answer|answer|ans|উত্তর)\s*=*\s*", "", normalized)
        for unit in self.normalizer.known_units:
            normalized = normalized.replace(unit.lower(), "")
        normalized = re.sub(r"(?<=\d)টি\b", "", normalized)
        normalized = normalized.replace(":", "/")
        normalized = re.sub(r"[\s,;।]+", "", normalized)
        return normalized.strip(".=")

    def _matches_accepted_answer(self, student_expression: str, problem_dag: ProblemReferenceDAG) -> bool:
        student = self._canonical_answer_text(student_expression)
        if not student:
            return False
        for answer in problem_dag.accepted_answer_forms:
            if student == self._canonical_answer_text(answer):
                return True
        return False

    def validate_ast(self, code_str: str) -> bool:
        """Ensures expression contains ONLY safe mathematical syntax."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if not isinstance(node, ALLOWED_AST_NODES):
                return False
            # Prevent string literals or non-numeric constants (e.g. '__import__', 'os', etc.)
            if isinstance(node, ast.Constant) and not isinstance(node.value, ALLOWED_CONSTANT_TYPES):
                return False
        return True

    def parse_safe_sympy(self, expr_str: str) -> Optional[sp.Expr]:
        """Safely parses mathematical expression into SymPy."""
        # Pre-clean string
        cleaned = expr_str.strip().replace("^", "**")
        if not self.validate_ast(cleaned):
            return None
        try:
            return parse_expr(cleaned, transformations=self.transformations, evaluate=False)
        except Exception:
            return None

    def _split_relation(self, expr_str: str) -> Tuple[Optional[str], str, str]:
        """Splits an expression by relational operators (<=, >=, <, >, ==, =)."""
        # Search in order of operator length to match '<=' before '<'
        for op in ["<=", ">=", "==", "<", ">", "="]:
            if op in expr_str:
                parts = expr_str.split(op, 1)
                norm_op = "=" if op == "==" else op
                return norm_op, parts[0].strip(), parts[1].strip()
        return None, expr_str.strip(), ""

    def verify_step(
        self,
        student_expression: str,
        problem_dag: Optional[ProblemReferenceDAG] = None,
        target_step_id: Optional[str] = None,
    ) -> VerificationResult:
        """Verifies a student's step against a reference problem specification.

        Outputs MathematicalStatus:
        - VALID: Step matches reference or an equivalent valid strategy.
        - INVALID: Step violates mathematical relations or matches a known error.
        - UNSUPPORTED: Step uses variables or operations outside supported reference domain.
        - UNVERIFIABLE: String cannot be safely parsed into a valid mathematical relation.
        """
        if not student_expression or not student_expression.strip():
            return VerificationResult(
                mathematical_status=MathematicalStatus.UNVERIFIABLE,
                interpretation_status=InterpretationStatus.UNRESOLVED,
                verification_reason="empty_or_whitespace_expression",
            )

        # 1. Normalize text and numerals (converts Bengali digits/operators to standard math)
        var_aliases = problem_dag.variable_aliases if problem_dag else None
        expr_str = self.normalizer.extract_expression(
            student_expression,
            variable_aliases=var_aliases,
        )

        if problem_dag is not None and problem_dag.accepted_answer_forms:
            if self._matches_accepted_answer(student_expression, problem_dag) or self._matches_accepted_answer(expr_str, problem_dag):
                return VerificationResult(
                    mathematical_status=MathematicalStatus.VALID,
                    interpretation_status=InterpretationStatus.SUPPORTED,
                    verification_reason="accepted_final_answer",
                    normalized_expression=expr_str,
                    matched_reference_step_id="final_answer",
                )
            if re.match(r"^\s*(?:final_answer|answer|ans)\s*=", expr_str, re.IGNORECASE):
                return VerificationResult(
                    mathematical_status=MathematicalStatus.INVALID,
                    interpretation_status=InterpretationStatus.SUPPORTED,
                    verification_reason="final_answer_mismatch",
                    normalized_expression=expr_str,
                    matched_reference_step_id="final_answer",
                )

        # 2. Split relational operator (if any)
        rel_op, lhs_str, rhs_str = self._split_relation(expr_str)

        # If there is a relation, ensure LHS identifier is clean for AST validation
        if rel_op is not None:
            if not re.search(r"[\+\-\*/\^]", lhs_str):
                lhs_str = re.sub(r"\s+", "_", lhs_str)
            ast_check_str = f"{lhs_str} == {rhs_str}" if rel_op == "=" else f"{lhs_str} {rel_op} {rhs_str}"
        else:
            ast_check_str = expr_str

        # 3. Strict AST sandboxing
        if not self.validate_ast(ast_check_str):
            return VerificationResult(
                mathematical_status=MathematicalStatus.UNVERIFIABLE,
                interpretation_status=InterpretationStatus.UNRESOLVED,
                verification_reason="unsafe_ast_or_syntax_error",
                normalized_expression=expr_str,
            )

        # 4. If no problem DAG is supplied, evaluate purely standalone consistency
        if problem_dag is None:
            if rel_op is not None:
                parsed_lhs = self.parse_safe_sympy(lhs_str)
                parsed_rhs = self.parse_safe_sympy(rhs_str)
                if parsed_lhs is None or parsed_rhs is None:
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.UNVERIFIABLE,
                        interpretation_status=InterpretationStatus.UNRESOLVED,
                        verification_reason="sympy_parse_failure",
                        normalized_expression=expr_str,
                    )
                if rel_op == "=":
                    diff = sp.simplify(parsed_lhs - parsed_rhs)
                    if diff == 0:
                        return VerificationResult(
                            mathematical_status=MathematicalStatus.VALID,
                            interpretation_status=InterpretationStatus.SUPPORTED,
                            verification_reason="symbolic_identity_verified",
                            normalized_expression=expr_str,
                        )
                    # If constant and non-zero diff -> invalid
                    if diff.is_number and diff != 0:
                        return VerificationResult(
                            mathematical_status=MathematicalStatus.INVALID,
                            interpretation_status=InterpretationStatus.SUPPORTED,
                            verification_reason="equality_not_satisfied",
                            normalized_expression=expr_str,
                        )
                    # If expression contains unbound symbols without DAG -> supported relation
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.VALID,
                        interpretation_status=InterpretationStatus.SUPPORTED,
                        verification_reason="well_formed_relation",
                        normalized_expression=expr_str,
                    )
                else:
                    # Inequations evaluation when constants
                    diff = sp.simplify(parsed_lhs - parsed_rhs)
                    if diff.is_number:
                        is_valid = False
                        if rel_op == "<=" and diff <= 0:
                            is_valid = True
                        elif rel_op == ">=" and diff >= 0:
                            is_valid = True
                        elif rel_op == "<" and diff < 0:
                            is_valid = True
                        elif rel_op == ">" and diff > 0:
                            is_valid = True
                        return VerificationResult(
                            mathematical_status=MathematicalStatus.VALID if is_valid else MathematicalStatus.INVALID,
                            interpretation_status=InterpretationStatus.SUPPORTED,
                            verification_reason="inequality_evaluated",
                            normalized_expression=expr_str,
                        )
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.VALID,
                        interpretation_status=InterpretationStatus.SUPPORTED,
                        verification_reason="well_formed_inequality",
                        normalized_expression=expr_str,
                    )
            else:
                parsed = self.parse_safe_sympy(expr_str)
                if parsed is not None:
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.VALID,
                        interpretation_status=InterpretationStatus.SUPPORTED,
                        verification_reason="well_formed_expression",
                        normalized_expression=expr_str,
                    )
                return VerificationResult(
                    mathematical_status=MathematicalStatus.UNVERIFIABLE,
                    interpretation_status=InterpretationStatus.UNRESOLVED,
                    verification_reason="cannot_parse_expression",
                    normalized_expression=expr_str,
                )

        # 5. We have a ProblemReferenceDAG: verify against reference specification
        # Step A: Check known error patterns first for precise diagnostic localization
        for step in problem_dag.reference_steps:
            for err_expr, err_reason in step.known_error_patterns.items():
                if self._check_equivalence(expr_str, err_expr):
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.INVALID,
                        interpretation_status=InterpretationStatus.SUPPORTED,
                        verification_reason=err_reason,
                        normalized_expression=expr_str,
                        matched_reference_step_id=step.step_id,
                    )

        # Step B: Check reference step canonical expressions and alternative forms
        for step in problem_dag.reference_steps:
            if target_step_id and step.step_id != target_step_id:
                continue

            # Check primary symbolic expression
            if self._check_equivalence(expr_str, step.symbolic_expression):
                return VerificationResult(
                    mathematical_status=MathematicalStatus.VALID,
                    interpretation_status=InterpretationStatus.SUPPORTED,
                    verification_reason=f"matches_step_{step.step_id}",
                    normalized_expression=expr_str,
                    matched_reference_step_id=step.step_id,
                )

            # Check known alternative forms
            for alt_expr in step.alternative_forms:
                if self._check_equivalence(expr_str, alt_expr):
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.VALID,
                        interpretation_status=InterpretationStatus.SUPPORTED,
                        verification_reason=f"matches_alternative_for_{step.step_id}",
                        normalized_expression=expr_str,
                        matched_reference_step_id=step.step_id,
                        is_alternative_strategy=True,
                    )

        # Step C: Check for valid alternative strategy or arithmetic violation
        if rel_op is not None:
            parsed_lhs = self.parse_safe_sympy(lhs_str)
            parsed_rhs = self.parse_safe_sympy(rhs_str)
            if parsed_lhs is not None and parsed_rhs is not None:
                symbols_present = [str(s) for s in parsed_lhs.free_symbols | parsed_rhs.free_symbols]
                unknown_symbols = [s for s in symbols_present if s not in problem_dag.declared_variables]
                if unknown_symbols:
                    return VerificationResult(
                        mathematical_status=MathematicalStatus.UNSUPPORTED,
                        interpretation_status=InterpretationStatus.UNRESOLVED,
                        verification_reason=f"undeclared_variables_{unknown_symbols}",
                        normalized_expression=expr_str,
                    )

                diff = sp.simplify(parsed_lhs - parsed_rhs)
                if rel_op == "=":
                    if diff == 0:
                        return VerificationResult(
                            mathematical_status=MathematicalStatus.VALID,
                            interpretation_status=InterpretationStatus.SUPPORTED,
                            verification_reason="valid_alternative_relation",
                            normalized_expression=expr_str,
                            is_alternative_strategy=True,
                        )
                    # Constant difference indicates arithmetic error
                    if diff.is_number and diff != 0:
                        return VerificationResult(
                            mathematical_status=MathematicalStatus.INVALID,
                            interpretation_status=InterpretationStatus.SUPPORTED,
                            verification_reason="relation_violated",
                            normalized_expression=expr_str,
                        )

                    # Check if this directly assigns a value to a step target_variable
                    # e.g. student writes 'new_quantity = 95', but reference step target is 'new_quantity = 80'
                    for step in problem_dag.reference_steps:
                        if target_step_id and step.step_id != target_step_id:
                            continue
                        if lhs_str == step.target_variable:
                            ref_op, ref_lhs, ref_rhs = self._split_relation(step.symbolic_expression)
                            if ref_op == "=":
                                ref_val = self.parse_safe_sympy(ref_rhs)
                                if ref_val is not None:
                                    step_diff = sp.simplify(parsed_rhs - ref_val)
                                    if step_diff.is_number and step_diff != 0:
                                        return VerificationResult(
                                            mathematical_status=MathematicalStatus.INVALID,
                                            interpretation_status=InterpretationStatus.SUPPORTED,
                                            verification_reason="relation_violated",
                                            normalized_expression=expr_str,
                                            matched_reference_step_id=step.step_id,
                                        )

        # Step could not be matched or resolved within supported domain
        return VerificationResult(
            mathematical_status=MathematicalStatus.UNSUPPORTED,
            interpretation_status=InterpretationStatus.UNRESOLVED,
            verification_reason="unrecognized_step_strategy",
            normalized_expression=expr_str,
        )

    def _check_equivalence(self, expr1_str: str, expr2_str: str) -> bool:
        """Determines if two equations, inequalities, or expressions are symbolically equivalent."""
        if expr1_str.strip() == expr2_str.strip():
            return True

        op1, lhs1_s, rhs1_s = self._split_relation(expr1_str)
        op2, lhs2_s, rhs2_s = self._split_relation(expr2_str)

        # Case 1: Both are relations (equations or inequalities)
        if op1 is not None and op2 is not None:
            lhs1, rhs1 = self.parse_safe_sympy(lhs1_s), self.parse_safe_sympy(rhs1_s)
            lhs2, rhs2 = self.parse_safe_sympy(lhs2_s), self.parse_safe_sympy(rhs2_s)
            if None in (lhs1, rhs1, lhs2, rhs2):
                return False

            diff1 = sp.simplify(lhs1 - rhs1)
            diff2 = sp.simplify(lhs2 - rhs2)

            if op1 == "=" and op2 == "=":
                if diff1 == diff2 or sp.simplify(diff1 + diff2) == 0:
                    return True
                # Proportional equivalence for equations with variables
                all_syms = diff1.free_symbols | diff2.free_symbols
                if all_syms:
                    try:
                        ratio = sp.simplify(diff1 / diff2)
                        if ratio.is_constant(*all_syms) and ratio != 0:
                            return True
                    except Exception:
                        pass
                return False

            # Inequations
            flip_map = {"<=": ">=", ">=": "<=", "<": ">", ">": "<"}
            if op1 == op2:
                if diff1 == diff2:
                    return True
                all_syms = diff1.free_symbols | diff2.free_symbols
                if all_syms:
                    try:
                        ratio = sp.simplify(diff1 / diff2)
                        if ratio.is_constant(*all_syms) and ratio > 0:
                            return True
                    except Exception:
                        pass
            elif op1 == flip_map.get(op2):
                if sp.simplify(diff1 + diff2) == 0:
                    return True
                all_syms = diff1.free_symbols | diff2.free_symbols
                if all_syms:
                    try:
                        ratio = sp.simplify(diff1 / diff2)
                        if ratio.is_constant(*all_syms) and ratio < 0:
                            return True
                    except Exception:
                        pass
            return False

        # Case 2: Both are pure expressions
        if op1 is None and op2 is None:
            sp1 = self.parse_safe_sympy(expr1_str)
            sp2 = self.parse_safe_sympy(expr2_str)
            if sp1 is not None and sp2 is not None:
                try:
                    return sp.simplify(sp1 - sp2) == 0
                except Exception:
                    return False

        return False
