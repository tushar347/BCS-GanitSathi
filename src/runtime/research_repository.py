from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from src.controller.schemas import CandidateCause, DiagnosticProbe
from src.normalizer.bengali_normalizer import BengaliNormalizer
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep


ALLOWED_TOPICS = {
    "percentages_profit_loss",
    "ratios_proportions",
    "work_time",
    "speed_distance",
    "averages_mixtures",
    "elementary_algebra_number_relations",
}


class RuntimeProblemContext(BaseModel):
    problem: Dict[str, Any]
    solution: Dict[str, Any] = Field(default_factory=dict)
    probes: List[Dict[str, Any]] = Field(default_factory=list)
    output_policy: Dict[str, Any] = Field(default_factory=dict)
    model_visible_histories: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchBenchmarkRepository:
    def __init__(self, dataset_root: str | Path = "data/raw_bcs/BCS_10-50_Dataset"):
        self.dataset_root = Path(dataset_root)
        self.normalizer = BengaliNormalizer()
        self._problems: Dict[str, Dict[str, Any]] = {}
        self._solutions: Dict[str, Dict[str, Any]] = {}
        self._probes: Dict[str, List[Dict[str, Any]]] = {}
        self._policies: Dict[str, Dict[str, Any]] = {}
        self._histories: Dict[str, List[Dict[str, Any]]] = {}
        self._loaded = False

    def load(self) -> int:
        self._problems.clear()
        self._solutions.clear()
        self._probes.clear()
        self._policies.clear()
        self._histories.clear()
        for folder in sorted(self.dataset_root.glob("BCS*")):
            research = folder / "research_benchmark"
            problems_path = research / "problems.json"
            if not problems_path.exists():
                continue
            problems = self._read_list(problems_path)
            solutions = self._read_list(research / "solutions.json")
            probes = self._read_list(research / "diagnostic_probes.json")
            policies = self._read_list(research / "output_policies.json")
            histories = self._read_list(research / "authored_histories_model_visible.json")
            for problem in problems:
                if not problem.get("in_scope", True):
                    continue
                if problem.get("topic_group") not in ALLOWED_TOPICS:
                    continue
                item_id = str(problem.get("item_id", ""))
                if item_id:
                    self._problems[item_id] = problem
            for row in solutions:
                item_id = str(row.get("item_id", ""))
                if item_id in self._problems:
                    self._solutions[item_id] = row
            for row in probes:
                item_id = str(row.get("item_id", ""))
                if item_id in self._problems:
                    self._probes.setdefault(item_id, []).append(row)
            for row in policies:
                item_id = str(row.get("item_id", ""))
                if item_id in self._problems:
                    self._policies[item_id] = row
            for row in histories:
                item_id = str(row.get("item_id", ""))
                if item_id in self._problems:
                    self._histories.setdefault(item_id, []).append(row)
        self._loaded = True
        return len(self._problems)

    def list_problems(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return [self._problems[k] for k in sorted(self._problems)]

    def get_context(self, item_id: str) -> RuntimeProblemContext:
        self._ensure_loaded()
        if item_id not in self._problems:
            raise KeyError(item_id)
        return RuntimeProblemContext(
            problem=self._problems[item_id],
            solution=self._solutions.get(item_id, {}),
            probes=self._probes.get(item_id, []),
            output_policy=self._policies.get(item_id, {}),
            model_visible_histories=self._histories.get(item_id, []),
        )

    def build_problem_dag(self, item_id: str) -> ProblemReferenceDAG:
        context = self.get_context(item_id)
        problem = context.problem
        solution = context.solution
        reference_steps: List[ReferenceStep] = []
        strategies = solution.get("reviewed_strategies", []) if isinstance(solution, dict) else []
        step_counter = 0
        for strategy in strategies:
            symbolic = list(strategy.get("symbolic_expressions", []) or [])
            textual_steps = list(strategy.get("steps", []) or [])
            for expression in symbolic:
                step_counter += 1
                reference_steps.append(
                    ReferenceStep(
                        step_id=f"strategy_{step_counter}",
                        description=textual_steps[min(step_counter - 1, len(textual_steps) - 1)] if textual_steps else "",
                        target_variable="answer",
                        symbolic_expression=str(expression),
                    )
                )
        accepted = [str(v) for v in problem.get("accepted_answer_forms", []) if str(v).strip()]
        symbolic_answer = self._first_symbolic_answer(accepted)
        if symbolic_answer:
            reference_steps.append(
                ReferenceStep(
                    step_id="final_answer",
                    description="accepted final answer",
                    target_variable="answer",
                    symbolic_expression=f"answer = {symbolic_answer}",
                )
            )
        return ProblemReferenceDAG(
            item_id=str(problem.get("item_id", item_id)),
            family_id=str(problem.get("family_id", item_id)),
            problem_text=str(problem.get("question_original", problem.get("question_normalized", ""))),
            declared_variables={"answer": "final answer"},
            reference_steps=reference_steps,
            accepted_answer_forms=accepted,
        )

    def build_diagnostic_probes(self, item_id: str) -> List[DiagnosticProbe]:
        context = self.get_context(item_id)
        result = []
        topic_group = str(context.problem.get("topic_group", ""))
        for row in context.probes:
            categories = [str(v) for v in row.get("response_categories", []) if str(v).strip()]
            if not categories:
                categories = ["supported", "unsupported", "ambiguous", "timeout"]
            primary_cause = CandidateCause.PERCENTAGE_BASE if topic_group == "percentages_profit_loss" else CandidateCause.CONCEPTUAL_ERROR
            candidate_causes = [primary_cause, CandidateCause.TRANSIENT_SLIP]
            response_model = self._default_response_model(categories, candidate_causes)
            burden = self._burden_seconds(row.get("expected_burden"))
            result.append(
                DiagnosticProbe(
                    probe_id=str(row.get("probe_id", f"{item_id}_probe")),
                    target_ambiguity=str(row.get("target_ambiguity", "unresolved_cause")),
                    prompt_bn=str(row.get("probe_bn", "ধাপটি সংক্ষেপে ব্যাখ্যা করো।")),
                    prompt_en=str(row.get("probe_en", "Explain the step briefly.")),
                    candidate_causes=candidate_causes,
                    response_model=response_model,
                    expected_burden_seconds=burden,
                )
            )
        return result

    def permitted_facts(self, item_id: str) -> List[str]:
        context = self.get_context(item_id)
        policy = context.output_policy
        facts = [str(v) for v in policy.get("permitted_facts", [])]
        if not facts:
            facts = ["problem_statement", "student_visible_work", "nondecisive mathematical relationships"]
        return facts

    def prohibited_answers(self, item_id: str) -> List[str]:
        context = self.get_context(item_id)
        return [str(v) for v in context.problem.get("accepted_answer_forms", []) if str(v).strip()]

    def worked_solution_steps(self, item_id: str) -> List[str]:
        context = self.get_context(item_id)
        steps = []
        for strategy in context.solution.get("reviewed_strategies", []) if context.solution else []:
            steps.extend(str(v) for v in strategy.get("steps", []) if str(v).strip())
        return steps

    def policy_allows(self, item_id: str, action_name: str) -> bool:
        context = self.get_context(item_id)
        permitted = {str(v) for v in context.output_policy.get("permitted_action", [])}
        if not permitted:
            return True
        aliases = {
            "give_conceptual_hint": "give_nondecisive_hint",
            "offer_local_scaffold": "give_nondecisive_hint",
            "request_independent_retry": "give_nondecisive_hint",
            "offer_transfer_question": "give_nondecisive_hint",
            "acknowledge_correct_step": "acknowledge_valid_step",
            "ask_clarification": "ask_clarification",
        }
        return action_name in permitted or aliases.get(action_name) in permitted

    def _default_response_model(
        self,
        categories: List[str],
        candidate_causes: List[CandidateCause],
    ) -> Dict[str, Dict[CandidateCause, float]]:
        result: Dict[str, Dict[CandidateCause, float]] = {}
        total = max(len(categories), 1)
        for index, category in enumerate(categories):
            label = category.lower()
            row: Dict[CandidateCause, float] = {}
            for cause in CandidateCause:
                value = 1.0 / total
                if cause in candidate_causes:
                    if any(token in label for token in ["incorrect", "error", "wrong_rule"]):
                        value = 0.65 if cause == CandidateCause.PERCENTAGE_BASE else 0.35
                    elif any(token in label for token in ["correct", "supported", "correct_rule"]):
                        value = 0.30 if cause == CandidateCause.PERCENTAGE_BASE else 0.70
                    elif any(token in label for token in ["slip", "calculation"]):
                        value = 0.20 if cause == CandidateCause.PERCENTAGE_BASE else 0.80
                    else:
                        value = 0.50
                elif cause == CandidateCause.UNRESOLVED:
                    value = 0.75 if any(token in label for token in ["ambiguous", "insufficient", "timeout", "skipped"] ) else 0.10
                elif cause == CandidateCause.NO_ERROR:
                    value = 0.75 if any(token in label for token in ["correct", "supported"] ) else 0.10
                row[cause] = max(value, 0.02)
            result[category] = row
        return result

    def _first_symbolic_answer(self, accepted: Iterable[str]) -> Optional[str]:
        for value in accepted:
            normalized = self.normalizer.normalize(value).normalized_text
            ratio = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*:\s*(-?\d+(?:\.\d+)?)\s*", normalized)
            if ratio:
                return f"({ratio.group(1)})/({ratio.group(2)})"
            number = re.search(r"-?\d+(?:\.\d+)?", normalized)
            if number and len(normalized) <= 24:
                return number.group(0)
        return None

    def _burden_seconds(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            number = re.search(r"\d+(?:\.\d+)?", value)
            if number:
                return float(number.group(0))
        return 15.0

    def _read_list(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, list) else []

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()
