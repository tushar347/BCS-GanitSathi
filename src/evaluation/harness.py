"""Evaluation harness for GonitSathi diagnostic controller.

Runs BCS dataset problem families through the full DiagnosticController pipeline,
collects evaluation metrics, timing profiles, and generates structured reports.

Conforms to RA3 responsibilities: evaluation metrics, latency calculations, and cost profiling.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.controller.diagnostic_controller import DiagnosticController
from src.controller.schemas import (
    AssistanceLevel,
    CandidateCause,
    ClaimStatus,
    MathematicalStatus,
)
from src.verifier.symbolic_verifier import ProblemReferenceDAG
from src.benchmark.loader import BenchmarkDatasetSchema, ProblemFamilySchema
from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.evaluation.profiler import PipelineProfiler
from src.evaluation.metrics import (
    calculate_unsupported_commit_risk,
    calculate_commitment_coverage,
    calculate_multiclass_brier_score,
    calculate_first_error_accuracy,
)


@dataclass
class FamilyEvaluationResult:
    """Result of evaluating one problem family."""
    family_id: str
    topic: str
    difficulty: str
    num_histories: int
    history_results: List[Dict[str, Any]] = field(default_factory=list)
    timing_ms: float = 0.0


@dataclass
class EvaluationReport:
    """Complete evaluation report across all problem families."""
    split: str
    total_families: int
    total_histories_run: int
    family_results: List[FamilyEvaluationResult] = field(default_factory=list)
    aggregate_metrics: Dict[str, Any] = field(default_factory=dict)
    latency_summary: Dict[str, Any] = field(default_factory=dict)
    per_topic_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "split": self.split,
            "total_families": self.total_families,
            "total_histories_run": self.total_histories_run,
            "aggregate_metrics": self.aggregate_metrics,
            "latency_summary": self.latency_summary,
            "per_topic_summary": self.per_topic_summary,
            "family_results": [
                {
                    "family_id": fr.family_id,
                    "topic": fr.topic,
                    "difficulty": fr.difficulty,
                    "num_histories": fr.num_histories,
                    "timing_ms": round(fr.timing_ms, 3),
                    "history_results": fr.history_results,
                }
                for fr in self.family_results
            ],
        }


class EvaluationHarness:
    """Runs the full evaluation pipeline on a BenchmarkDatasetSchema."""

    def __init__(
        self,
        activation_threshold: float = 0.80,
        retention_threshold: float = 0.40,
        entropy_threshold: float = 0.40,
    ):
        self.activation_threshold = activation_threshold
        self.retention_threshold = retention_threshold
        self.entropy_threshold = entropy_threshold
        self.profiler = PipelineProfiler()

    def evaluate_dataset(
        self,
        dataset: BenchmarkDatasetSchema,
        ingester: BCSDatasetIngester,
        max_families: Optional[int] = None,
    ) -> EvaluationReport:
        """Run evaluation across all problem families in the dataset."""
        families = dataset.families
        if max_families is not None:
            families = families[:max_families]

        report = EvaluationReport(
            split=dataset.split,
            total_families=len(families),
            total_histories_run=0,
        )

        all_predictions: List[Dict[CandidateCause, float]] = []
        all_ground_truths: List[CandidateCause] = []
        all_first_error_preds: List[Optional[str]] = []
        all_first_error_truths: List[Optional[str]] = []
        all_active_commitments: List[Dict[str, str]] = []
        adjudicated_labels: Dict[str, str] = {}
        topic_stats: Dict[str, Dict[str, int]] = {}

        step_counter = 0

        for family in families:
            family_start = time.perf_counter()

            # Build the ProblemReferenceDAG for this family
            dag = ingester.build_problem_dag(family.item_id)
            if dag is None:
                # Fall back to building from schema data directly
                dag = self._dag_from_family_schema(family)

            family_result = FamilyEvaluationResult(
                family_id=family.family_id,
                topic=family.topic,
                difficulty=family.difficulty,
                num_histories=len(family.attempt_histories),
            )

            # Track per-topic stats
            if family.topic not in topic_stats:
                topic_stats[family.topic] = {"total": 0, "correct": 0, "errors": 0}
            topic_stats[family.topic]["total"] += 1

            for history in family.attempt_histories:
                # Fresh controller per history
                controller = DiagnosticController(
                    activation_threshold=self.activation_threshold,
                    retention_threshold=self.retention_threshold,
                    entropy_threshold=self.entropy_threshold,
                )

                history_result: Dict[str, Any] = {
                    "history_id": history.history_id,
                    "history_type": history.history_type,
                    "latent_cause": history.latent_cause.value if history.latent_cause else None,
                    "steps": [],
                }

                first_error_step: Optional[str] = None
                predicted_first_error: Optional[str] = None

                for event in history.events:
                    step_counter += 1
                    raw_text = event.get("text", "")
                    assistance = AssistanceLevel(
                        event.get("assistance_level", "none")
                    )
                    group_id = event.get(
                        "independent_evidence_group",
                        f"grp_{uuid.uuid4().hex[:8]}"
                    )

                    # Profile this step
                    self.profiler.begin_step(step_counter, family.family_id, family.item_id)

                    self.profiler.begin_stage("normalize")
                    # Run through pipeline
                    try:
                        action, audit, obs = controller.process_student_step(
                            raw_text=raw_text,
                            problem_dag=dag,
                            learner_id=f"eval_{history.history_id}",
                            independent_group_id=group_id,
                            assistance_level=assistance,
                        )
                    except Exception as e:
                        self.profiler.end_stage("normalize")
                        self.profiler.end_step()
                        history_result["steps"].append({
                            "text": raw_text,
                            "error": str(e),
                        })
                        continue
                    self.profiler.end_stage("pipeline")

                    profile = self.profiler.end_step()

                    step_result = {
                        "text": raw_text,
                        "mathematical_status": obs.mathematical_status.value,
                        "evidence_admitted": obs.evidence_admitted,
                        "action_type": action.action_type.value,
                        "top_belief": None,
                        "entropy": round(controller.belief_updater.get_normalized_entropy(), 4),
                    }

                    top_cause, top_prob = controller.belief_updater.get_top_candidate()
                    step_result["top_belief"] = {
                        "cause": top_cause.value,
                        "probability": round(top_prob, 4),
                    }

                    if profile:
                        step_result["latency_ms"] = round(profile.total_ms, 3)

                    history_result["steps"].append(step_result)

                    # Track first error
                    if (obs.mathematical_status == MathematicalStatus.INVALID
                            and predicted_first_error is None):
                        predicted_first_error = obs.verification_reason

                # Record final beliefs for this history
                final_beliefs = dict(controller.belief_updater.beliefs)
                history_result["final_beliefs"] = {
                    k.value: round(v, 4) for k, v in final_beliefs.items()
                }

                # Collect metrics data
                if history.latent_cause is not None:
                    all_predictions.append(final_beliefs)
                    all_ground_truths.append(history.latent_cause)

                    # Track first error ground truth
                    if history.latent_cause != CandidateCause.NO_ERROR:
                        first_error_step = history.history_type
                        topic_stats[family.topic]["errors"] += 1
                    else:
                        topic_stats[family.topic]["correct"] += 1

                    all_first_error_preds.append(predicted_first_error)
                    all_first_error_truths.append(first_error_step)

                # Collect active commitments
                for cause, hyp in controller.belief_updater.active_hypotheses.items():
                    if hyp.status == ClaimStatus.ACTIVE:
                        all_active_commitments.append({
                            "learner_id": f"eval_{history.history_id}",
                            "item_id": family.item_id,
                            "cause": cause.value,
                        })
                        key = f"eval_{history.history_id}:{family.item_id}"
                        if history.latent_cause:
                            adjudicated_labels[key] = history.latent_cause.value

                family_result.history_results.append(history_result)
                report.total_histories_run += 1

            family_result.timing_ms = (time.perf_counter() - family_start) * 1000
            report.family_results.append(family_result)

        # Compute aggregate metrics
        report.aggregate_metrics = self._compute_aggregate_metrics(
            all_predictions, all_ground_truths,
            all_first_error_preds, all_first_error_truths,
            all_active_commitments, adjudicated_labels,
        )

        report.latency_summary = self.profiler.get_summary()
        report.per_topic_summary = topic_stats

        return report

    def _compute_aggregate_metrics(
        self,
        predictions: List[Dict[CandidateCause, float]],
        ground_truths: List[CandidateCause],
        first_error_preds: List[Optional[str]],
        first_error_truths: List[Optional[str]],
        active_commitments: List[Dict[str, str]],
        adjudicated_labels: Dict[str, str],
    ) -> Dict[str, Any]:
        """Compute all Section 10.1/10.2 evaluation metrics."""
        metrics: Dict[str, Any] = {}

        # Multiclass Brier score
        if predictions and ground_truths:
            metrics["multiclass_brier_score"] = round(
                calculate_multiclass_brier_score(predictions, ground_truths), 4
            )

        # First-error accuracy
        if first_error_preds:
            metrics["first_error_accuracy"] = round(
                calculate_first_error_accuracy(first_error_preds, first_error_truths), 4
            )

        # Unsupported-commit risk
        ucr = calculate_unsupported_commit_risk(active_commitments, adjudicated_labels)
        if ucr is not None:
            metrics["unsupported_commit_risk"] = round(ucr, 4)

        # Commitment coverage
        if predictions:
            metrics["commitment_coverage"] = round(
                calculate_commitment_coverage(active_commitments, len(predictions)), 4
            )

        metrics["total_evaluated"] = len(predictions)
        metrics["total_active_commitments"] = len(active_commitments)

        return metrics

    def _dag_from_family_schema(self, family: ProblemFamilySchema) -> ProblemReferenceDAG:
        """Fallback: build a ProblemReferenceDAG directly from the schema."""
        from src.verifier.symbolic_verifier import ReferenceStep as VerifierReferenceStep

        ref_steps = [
            VerifierReferenceStep(
                step_id=s.step_id,
                description=f"Step {s.step_id}",
                target_variable="answer",
                symbolic_expression=s.symbolic_expression,
                alternative_forms=s.alternative_forms,
                known_error_patterns=s.known_error_patterns,
            )
            for s in family.reference_steps
        ]

        return ProblemReferenceDAG(
            item_id=family.item_id,
            family_id=family.family_id,
            problem_text=family.question_bn,
            declared_variables=family.declared_variables,
            variable_aliases=family.variable_aliases,
            reference_steps=ref_steps,
        )
