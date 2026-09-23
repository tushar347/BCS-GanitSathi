"""Comparative evaluation runner across Baselines B0-B3 and GonitSathi (G).

Evaluates any BaseTutor on a BenchmarkDatasetSchema and calculates:
- Unsupported-commit risk (R_commit)
- Commitment coverage (C_commit)
- Multiclass Brier score (BS)
- First-error accuracy (A_FE)
- Efficiency profiling (latency, neural calls, symbolic calls, token count)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.baselines.base import BaseTutor
from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.benchmark.loader import BenchmarkDatasetSchema
from src.controller.schemas import AssistanceLevel, CandidateCause
from src.evaluation.metrics import (
    calculate_commitment_coverage,
    calculate_first_error_accuracy,
    calculate_multiclass_brier_score,
    calculate_unsupported_commit_risk,
)


@dataclass
class ComparativeEvaluationReport:
    """Evaluation report for a specific tutoring baseline."""
    system_name: str
    split: str
    total_families: int
    total_histories: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    resource_stats: Dict[str, Any] = field(default_factory=dict)
    family_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_name": self.system_name,
            "split": self.split,
            "total_families": self.total_families,
            "total_histories": self.total_histories,
            "metrics": self.metrics,
            "resource_stats": self.resource_stats,
        }


class ComparativeHarness:
    """Runs any BaseTutor through the benchmark dataset."""

    def evaluate_tutor(
        self,
        tutor: BaseTutor,
        dataset: BenchmarkDatasetSchema,
        ingester: BCSDatasetIngester,
        max_families: Optional[int] = None,
    ) -> ComparativeEvaluationReport:
        families = dataset.families[:max_families] if max_families else dataset.families

        all_predictions: List[Dict[CandidateCause, float]] = []
        all_ground_truths: List[CandidateCause] = []
        all_first_error_preds: List[Optional[str]] = []
        all_first_error_truths: List[Optional[str]] = []
        all_active_commitments: List[Dict[str, str]] = []
        adjudicated_labels: Dict[str, str] = {}

        total_latency_ms = 0.0
        total_neural_calls = 0
        total_symbolic_calls = 0
        total_tokens = 0
        step_count = 0
        histories_count = 0

        family_results: List[Dict[str, Any]] = []

        for family in families:
            dag = ingester.build_problem_dag(family.item_id)
            if dag is None:
                continue

            fam_result = {
                "family_id": family.family_id,
                "item_id": family.item_id,
                "topic": family.topic,
                "histories": [],
            }

            for history in family.attempt_histories:
                histories_count += 1
                tutor.reset(learner_id=f"eval_{history.history_id}", problem_dag=dag)

                hist_res = {
                    "history_id": history.history_id,
                    "latent_cause": history.latent_cause.value if history.latent_cause else None,
                    "steps": [],
                }

                predicted_first_err = None
                last_beliefs = {}

                for event in history.events:
                    step_count += 1
                    raw_text = event.get("text", "")
                    assistance = AssistanceLevel(event.get("assistance_level", "none"))
                    group_id = event.get("independent_evidence_group")

                    step_res = tutor.process_student_step(
                        raw_text=raw_text,
                        problem_dag=dag,
                        assistance_level=assistance,
                        independent_group_id=group_id,
                    )

                    total_latency_ms += step_res.latency_ms
                    total_neural_calls += step_res.neural_calls
                    total_symbolic_calls += step_res.symbolic_calls
                    total_tokens += step_res.tokens_generated

                    last_beliefs = step_res.beliefs
                    if step_res.is_first_error and predicted_first_err is None:
                        predicted_first_err = step_res.first_error_reason or (
                            step_res.predicted_cause.value if step_res.predicted_cause else None
                        )

                    for commit in step_res.active_commitments:
                        all_active_commitments.append(commit)
                        key = f"{commit.get('learner_id')}:{commit.get('item_id')}"
                        if history.latent_cause:
                            adjudicated_labels[key] = history.latent_cause.value

                    hist_res["steps"].append({
                        "raw_text": raw_text,
                        "action_type": step_res.action.action_type.value,
                        "payload": step_res.action.payload,
                        "status": step_res.mathematical_status.value,
                    })

                # Record predictions for Brier score
                if history.latent_cause is not None and last_beliefs:
                    all_predictions.append(last_beliefs)
                    all_ground_truths.append(history.latent_cause)

                # Record first error truth & pred
                if history.latent_cause is not None:
                    first_err_truth = history.history_type if history.latent_cause != CandidateCause.NO_ERROR else None
                    all_first_error_preds.append(predicted_first_err)
                    all_first_error_truths.append(first_err_truth)

                fam_result["histories"].append(hist_res)

            family_results.append(fam_result)

        # Calculate metrics
        metrics: Dict[str, Any] = {}
        if all_predictions and all_ground_truths:
            metrics["multiclass_brier_score"] = round(
                calculate_multiclass_brier_score(all_predictions, all_ground_truths), 4
            )
        else:
            metrics["multiclass_brier_score"] = "NA"

        if all_first_error_preds:
            metrics["first_error_accuracy"] = round(
                calculate_first_error_accuracy(all_first_error_preds, all_first_error_truths), 4
            )

        ucr = calculate_unsupported_commit_risk(all_active_commitments, adjudicated_labels)
        metrics["unsupported_commit_risk"] = round(ucr, 4) if ucr is not None else 0.0
        metrics["commitment_coverage"] = round(
            calculate_commitment_coverage(all_active_commitments, histories_count), 4
        )
        metrics["total_commitments"] = len(all_active_commitments)

        resource_stats = {
            "avg_latency_ms": round(total_latency_ms / max(1, step_count), 2),
            "total_neural_calls": total_neural_calls,
            "total_symbolic_calls": total_symbolic_calls,
            "total_tokens_generated": total_tokens,
            "total_steps": step_count,
        }

        return ComparativeEvaluationReport(
            system_name=tutor.name,
            split=dataset.split,
            total_families=len(families),
            total_histories=histories_count,
            metrics=metrics,
            resource_stats=resource_stats,
            family_results=family_results,
        )
