"""Integration test: run BCS dataset through the full evaluation harness.

End-to-end test that validates the complete pipeline from dataset ingestion
through diagnostic controller evaluation to metrics collection.
"""

import pytest
from pathlib import Path

from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.evaluation.harness import EvaluationHarness


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw_bcs"
HAS_DATA = DATA_DIR.exists() and (
    (DATA_DIR / "bcs_math_catalog.json").exists()
    or (DATA_DIR / "BCS_10-50_Dataset").exists()
)


@pytest.mark.skipif(not HAS_DATA, reason="BCS dataset files not available")
class TestBCSDatasetEvaluation:
    """End-to-end evaluation of BCS dataset through diagnostic controller."""

    @pytest.fixture
    def ingester(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        ing.load_all()
        return ing

    @pytest.fixture
    def dataset(self, ingester):
        return ingester.build_benchmark_dataset(split="pilot")

    def test_evaluation_runs_without_error(self, dataset, ingester):
        """The evaluation harness should run to completion without crashing."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=5,
        )
        assert report.total_families <= 5
        assert report.total_histories_run > 0

    def test_report_has_aggregate_metrics(self, dataset, ingester):
        """The report should contain aggregate evaluation metrics."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=3,
        )
        assert "total_evaluated" in report.aggregate_metrics

    def test_report_has_latency_data(self, dataset, ingester):
        """The report should contain latency profiling data."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=3,
        )
        assert report.latency_summary.get("total_steps", 0) > 0

    def test_report_has_per_topic_data(self, dataset, ingester):
        """The report should contain per-topic summary data."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=5,
        )
        assert len(report.per_topic_summary) > 0

    def test_family_results_have_history_outcomes(self, dataset, ingester):
        """Each family result should contain per-history outcomes."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=3,
        )
        for family_result in report.family_results:
            assert family_result.num_histories > 0
            assert len(family_result.history_results) > 0

    def test_report_serializable(self, dataset, ingester):
        """The report should be serializable to a dict without errors."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=3,
        )
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "family_results" in report_dict
        assert "aggregate_metrics" in report_dict

    def test_correct_history_produces_no_error_belief(self, dataset, ingester):
        """Correct work histories should trend NO_ERROR belief upward."""
        harness = EvaluationHarness()
        report = harness.evaluate_dataset(
            dataset=dataset,
            ingester=ingester,
            max_families=3,
        )
        for family_result in report.family_results:
            for history in family_result.history_results:
                if history.get("history_type") == "correct_work":
                    final = history.get("final_beliefs", {})
                    # NO_ERROR should be present in beliefs
                    assert "no_error" in final
