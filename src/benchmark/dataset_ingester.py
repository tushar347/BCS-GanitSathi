"""BCS Math Dataset Ingester for GonitSathi.

Reads RA2's BCS JSON datasets and constructs ProblemReferenceDAG objects
suitable for the DiagnosticController pipeline.

Supports:
1. Hierarchical dataset: data/raw_bcs/BCS_10-50_Dataset/ (BCS10..BCS50)
   - compatibility_demo_format/ (*_questions.json, *_answers.json)
   - research_benchmark/ (problems.json, solutions.json, etc.)
   - bcs*_json/ (e.g. BCS40..BCS45)
2. Flat legacy files: BCS_questiions.json, BCS_answers.json, bcs_math_catalog.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.normalizer.bengali_normalizer import BengaliNormalizer, BN_TO_EN_DIGITS
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep
from src.controller.schemas import CandidateCause
from src.benchmark.loader import (
    BenchmarkDatasetSchema,
    ProblemFamilySchema,
    AttemptHistorySchema,
    ReferenceStepSchema,
)


# Mapping from RA2 error type codes to GonitSathi CandidateCause
ERROR_TYPE_TO_CAUSE = {
    "conceptual": CandidateCause.PERCENTAGE_BASE,
    "arithmetic": CandidateCause.TRANSIENT_SLIP,
    "arithmetic_or_transcription": CandidateCause.TRANSIENT_SLIP,
    "interpretation": CandidateCause.LINGUISTIC_SLIP,
    "interface": CandidateCause.INTERFACE_SLIP,
    "unresolved": CandidateCause.UNRESOLVED,
    "no_error": CandidateCause.NO_ERROR,
}


def _bn_to_ascii_digits(text: str) -> str:
    """Convert Bengali digits in a string to ASCII digits."""
    return "".join(BN_TO_EN_DIGITS.get(ch, ch) for ch in text)


def _extract_numeric_answer(answer_text: Optional[str]) -> Optional[str]:
    """Extract the numeric value from an answer string like '৭২০ টাকা' or '128 meters'."""
    if not answer_text or not isinstance(answer_text, str):
        return None

    # Try Bengali digits first
    bn_match = re.search(r"[০-৯][০-৯,\.]*", answer_text)
    if bn_match:
        return _bn_to_ascii_digits(bn_match.group(0).replace(",", ""))

    # Try ASCII digits
    en_match = re.search(r"\d[\d,\.]*", answer_text)
    if en_match:
        return en_match.group(0).replace(",", "")

    return None


class BCSDatasetIngester:
    """Ingests RA2's BCS math JSON files and builds GonitSathi-compatible structures."""

    def __init__(self, data_dir: Optional[Union[Path, str]] = None):
        base_dir = Path(data_dir) if data_dir else Path("data/raw_bcs")
        # If user passed data/raw_bcs but BCS_10-50_Dataset exists, set dataset_root
        if (base_dir / "BCS_10-50_Dataset").exists():
            self.dataset_root = base_dir / "BCS_10-50_Dataset"
        else:
            self.dataset_root = base_dir
        self.data_dir = base_dir

        self.normalizer = BengaliNormalizer()
        self.questions: Dict[str, Dict[str, Any]] = {}
        self.answers: Dict[str, Dict[str, Any]] = {}
        self.catalog: Dict[str, Dict[str, Any]] = {}

    def load_questions(self, filepath: Optional[Path] = None) -> int:
        """Load questions from specified file or search in data_dir / dataset_root."""
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                fid = item.get("family_id", "")
                if fid:
                    self.questions[fid] = item
            return len(self.questions)

        # Look for legacy flat file
        legacy_path = self.data_dir / "BCS_questiions.json"
        if legacy_path.exists():
            return self.load_questions(legacy_path)

        # Look in BCS_10-50_Dataset
        if self.dataset_root.exists():
            for q_file in self.dataset_root.glob("*/*/*_questions.json"):
                try:
                    with open(q_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            fid = item.get("family_id", "")
                            if fid and fid not in self.questions:
                                self.questions[fid] = item
                except Exception:
                    continue

        return len(self.questions)

    def load_answers(self, filepath: Optional[Path] = None) -> int:
        """Load answers from specified file or search in data_dir / dataset_root."""
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                fid = item.get("family_id", "")
                if fid:
                    self.answers[fid] = item
            return len(self.answers)

        # Look for legacy flat file
        legacy_path = self.data_dir / "BCS_answers.json"
        if legacy_path.exists():
            return self.load_answers(legacy_path)

        # Look in BCS_10-50_Dataset
        if self.dataset_root.exists():
            for a_file in self.dataset_root.glob("*/*/*_answers.json"):
                try:
                    with open(a_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            fid = item.get("family_id", "")
                            if fid and fid not in self.answers:
                                self.answers[fid] = item
                except Exception:
                    continue

        return len(self.answers)

    def load_catalog(self, filepath: Optional[Path] = None) -> int:
        """Load catalog from specified file or compose from loaded questions & answers."""
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                fid = item.get("family_id", "")
                if fid:
                    self.catalog[fid] = item
            return len(self.catalog)

        # Look for legacy flat file
        legacy_path = self.data_dir / "bcs_math_catalog.json"
        if legacy_path.exists():
            return self.load_catalog(legacy_path)

        # If questions & answers are not loaded, load them
        if not self.questions:
            self.load_questions()
        if not self.answers:
            self.load_answers()

        # Build merged catalog in memory
        for fid, q in self.questions.items():
            ans = self.answers.get(fid, {})
            merged = dict(q)
            if "possible_mistakes" in ans:
                merged["annotated_error_catalog"] = ans["possible_mistakes"]
            self.catalog[fid] = merged

        return len(self.catalog)

    def load_all(self) -> Dict[str, int]:
        """Load all available dataset files. Returns counts per category."""
        counts = {}
        q_count = self.load_questions()
        if q_count > 0:
            counts["questions"] = q_count

        a_count = self.load_answers()
        if a_count > 0:
            counts["answers"] = a_count

        c_count = self.load_catalog()
        if c_count > 0:
            counts["catalog"] = c_count

        return counts

    def build_problem_dag(self, family_id: str) -> Optional[ProblemReferenceDAG]:
        """Build a ProblemReferenceDAG from catalog entry (or question+answer pair)."""
        entry = self.catalog.get(family_id) or self.questions.get(family_id)
        if not entry:
            return None

        answer_entry = self.answers.get(
            entry.get("raw_source_id", family_id),
            self.answers.get(family_id, {})
        )

        question_bn = entry.get("question_bn", entry.get("question_original", ""))
        solution_steps = entry.get("solution_steps", [])

        # Build declared variables from solution context
        target_quantity = entry.get("target_quantity", "answer")
        declared_variables = {
            "answer": str(target_quantity),
        }

        # Build reference steps from solution_steps
        reference_steps: List[ReferenceStep] = []
        for i, step_text in enumerate(solution_steps):
            step_id = f"step_{i + 1}"
            latex_spans = self.normalizer.extract_latex_spans(step_text)
            symbolic_expr = ""
            if latex_spans:
                rel_spans = [s for s in latex_spans if "=" in s]
                symbolic_expr = rel_spans[-1] if rel_spans else latex_spans[-1]
                symbolic_expr = re.sub(r"\\(?:times|cdot)", "*", symbolic_expr)
                symbolic_expr = re.sub(r"\\div", "/", symbolic_expr)
                symbolic_expr = re.sub(r"\\(?:text|mathrm)\{[^}]*\}", "", symbolic_expr)
                symbolic_expr = re.sub(r"\\approx", "=", symbolic_expr)
                symbolic_expr = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", symbolic_expr)
                symbolic_expr = re.sub(r"[\{\}]", "", symbolic_expr)
                symbolic_expr = symbolic_expr.strip()

            reference_steps.append(
                ReferenceStep(
                    step_id=step_id,
                    description=step_text[:100],
                    target_variable="answer" if i == len(solution_steps) - 1 else f"intermediate_{i + 1}",
                    symbolic_expression=symbolic_expr,
                )
            )

        # Build known error patterns from answer entry
        error_catalog = answer_entry.get("possible_mistakes", []) or entry.get("annotated_error_catalog", [])
        known_error_patterns: Dict[str, str] = {}
        for err in error_catalog:
            wrong_ans = err.get("wrong_answer", "")
            err_type = err.get("type", "unknown")
            err_code = err.get("code", f"error_{err_type}")
            if wrong_ans:
                wrong_num = _extract_numeric_answer(wrong_ans) or wrong_ans
                known_error_patterns[f"answer = {wrong_num}"] = f"{err_code}_{err_type}"

        # Attach error patterns to the final reference step
        if reference_steps and known_error_patterns:
            reference_steps[-1].known_error_patterns = known_error_patterns

        # Build variable aliases from glossary
        variable_aliases: Dict[str, List[str]] = {}
        glossary = entry.get("english_glossary", {})
        if glossary and isinstance(glossary, dict):
            for bn_term, en_term in glossary.items():
                canonical = re.sub(r"\s+", "_", en_term.lower())
                if canonical not in variable_aliases:
                    variable_aliases[canonical] = []
                variable_aliases[canonical].append(bn_term)
                declared_variables[canonical] = en_term

        return ProblemReferenceDAG(
            item_id=entry.get("item_id", family_id),
            family_id=entry.get("family_id", family_id),
            problem_text=question_bn,
            declared_variables=declared_variables,
            variable_aliases=variable_aliases,
            reference_steps=reference_steps,
        )

    def build_all_dags(self) -> List[ProblemReferenceDAG]:
        """Build ProblemReferenceDAGs for all loaded entries."""
        all_ids = sorted(self.catalog.keys()) if self.catalog else sorted(self.questions.keys())
        dags = []
        for fid in all_ids:
            dag = self.build_problem_dag(fid)
            if dag is not None:
                dags.append(dag)
        return dags

    def build_attempt_histories(self, family_id: str) -> List[AttemptHistorySchema]:
        """Build attempt histories from answer entries for a given family."""
        catalog_entry = self.catalog.get(family_id, {})
        raw_id = catalog_entry.get("raw_source_id", family_id)
        answer_entry = self.answers.get(raw_id) or self.answers.get(family_id, {})
        error_catalog = (
            answer_entry.get("possible_mistakes", [])
            or catalog_entry.get("annotated_error_catalog", [])
        )

        histories = []

        # History 1: Correct work
        correct_answer = answer_entry.get("correct_answer", "") or catalog_entry.get("correct_answer", "")
        correct_num = _extract_numeric_answer(correct_answer) or correct_answer
        histories.append(
            AttemptHistorySchema(
                history_id=f"{family_id}_correct",
                history_type="correct_work",
                events=[
                    {
                        "text": f"answer = {correct_num}",
                        "assistance_level": "none",
                        "independent_evidence_group": f"grp_{family_id}_correct",
                    }
                ],
                latent_cause=CandidateCause.NO_ERROR,
            )
        )

        # History per error type
        for err in error_catalog:
            err_type = err.get("type", "unknown")
            wrong_answer = err.get("wrong_answer", "")
            wrong_num = _extract_numeric_answer(wrong_answer) or wrong_answer
            cause = ERROR_TYPE_TO_CAUSE.get(err_type, CandidateCause.UNRESOLVED)

            histories.append(
                AttemptHistorySchema(
                    history_id=f"{family_id}_{err_type}",
                    history_type=f"{err_type}_error",
                    events=[
                        {
                            "text": f"answer = {wrong_num}",
                            "assistance_level": "none",
                            "independent_evidence_group": f"grp_{family_id}_{err_type}",
                        }
                    ],
                    latent_cause=cause,
                )
            )

        return histories

    def get_split_manifest(self) -> Optional[Dict[str, Any]]:
        """Load split manifest if available in data/manifests/."""
        possible_paths = [
            self.data_dir.parent / "manifests" / "split_manifest.json",
            Path("data/manifests/split_manifest.json"),
        ]
        for p in possible_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return None

    def build_benchmark_dataset(
        self,
        split: str = "all",
        family_ids: Optional[List[str]] = None,
        use_manifest: bool = False,
    ) -> BenchmarkDatasetSchema:
        """Build a complete BenchmarkDatasetSchema from loaded data."""
        if family_ids:
            all_ids = family_ids
        elif use_manifest and split in ("train", "dev", "test"):
            manifest = self.get_split_manifest()
            if manifest and "splits" in manifest and split in manifest["splits"]:
                all_ids = [fid for fid in manifest["splits"][split] if fid in self.catalog or fid in self.questions]
            else:
                all_ids = sorted(self.catalog.keys()) if self.catalog else sorted(self.questions.keys())
        elif self.catalog:
            all_ids = sorted(self.catalog.keys())
        else:
            all_ids = sorted(self.questions.keys())
        families = []

        for fid in all_ids:
            entry = self.catalog.get(fid) or self.questions.get(fid)
            if not entry:
                continue

            dag = self.build_problem_dag(fid)
            if not dag:
                continue

            histories = self.build_attempt_histories(fid)

            ref_steps_schema = [
                ReferenceStepSchema(
                    step_id=s.step_id,
                    symbolic_expression=s.symbolic_expression,
                    alternative_forms=s.alternative_forms,
                    known_error_patterns=s.known_error_patterns,
                )
                for s in dag.reference_steps
            ]

            families.append(
                ProblemFamilySchema(
                    item_id=dag.item_id,
                    family_id=dag.family_id,
                    topic=entry.get("topic", entry.get("topic_group", "unknown")),
                    difficulty=str(entry.get("difficulty", entry.get("difficulty_rating", "Medium"))),
                    question_bn=dag.problem_text,
                    declared_variables=dag.declared_variables,
                    variable_aliases=dag.variable_aliases,
                    reference_steps=ref_steps_schema,
                    attempt_histories=histories,
                )
            )

        return BenchmarkDatasetSchema(split=split, families=families)

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of loaded data."""
        topics = {}
        for entry in self.catalog.values():
            topic = entry.get("topic", entry.get("topic_group", "unknown"))
            topics[topic] = topics.get(topic, 0) + 1

        return {
            "questions_loaded": len(self.questions),
            "answers_loaded": len(self.answers),
            "catalog_loaded": len(self.catalog),
            "topics": topics,
        }
