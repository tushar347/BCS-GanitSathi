"""Tests for BCS dataset ingestion pipeline.

Validates that RA2's raw BCS JSON files can be loaded, parsed,
and converted into GonitSathi ProblemReferenceDAGs and BenchmarkDatasetSchemas.
"""

import pytest
from pathlib import Path
from src.benchmark.dataset_ingester import BCSDatasetIngester, _extract_numeric_answer


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_bcs"
HAS_DATA = DATA_DIR.exists() and (
    (DATA_DIR / "bcs_math_catalog.json").exists()
    or (DATA_DIR / "BCS_10-50_Dataset").exists()
)


class TestNumericExtraction:
    """Test the answer number extraction helper."""

    def test_bengali_number_extraction(self):
        assert _extract_numeric_answer("৭২০ টাকা") == "720"

    def test_bengali_comma_number(self):
        assert _extract_numeric_answer("৬,০০০ টাকা") == "6000"

    def test_english_number_extraction(self):
        assert _extract_numeric_answer("128 meters") == "128"

    def test_decimal_number(self):
        assert _extract_numeric_answer("8.333 quintals") == "8.333"

    def test_no_number(self):
        assert _extract_numeric_answer("no number here") is None


@pytest.mark.skipif(not HAS_DATA, reason="BCS dataset files not available")
class TestDatasetLoading:
    """Test loading RA2's BCS dataset files."""

    @pytest.fixture
    def ingester(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        ing.load_all()
        return ing

    def test_load_questions(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        count = ing.load_questions()
        assert count > 0

    def test_load_answers(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        count = ing.load_answers()
        assert count > 0

    def test_load_catalog(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        count = ing.load_catalog()
        assert count > 0

    def test_load_all_returns_counts(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        counts = ing.load_all()
        assert "questions" in counts or "catalog" in counts

    def test_summary(self, ingester):
        summary = ingester.get_summary()
        assert summary["catalog_loaded"] > 0
        assert len(summary["topics"]) > 0


@pytest.mark.skipif(not HAS_DATA, reason="BCS dataset files not available")
class TestDAGConstruction:
    """Test building ProblemReferenceDAGs from loaded data."""

    @pytest.fixture
    def ingester(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        ing.load_all()
        return ing

    def test_build_single_dag(self, ingester):
        # Use a known catalog family_id
        all_ids = list(ingester.catalog.keys())
        assert len(all_ids) > 0

        dag = ingester.build_problem_dag(all_ids[0])
        assert dag is not None
        assert dag.family_id == all_ids[0] or dag.item_id == all_ids[0]
        assert len(dag.problem_text) > 0

    def test_dag_has_reference_steps(self, ingester):
        all_ids = list(ingester.catalog.keys())
        dag = ingester.build_problem_dag(all_ids[0])
        assert dag is not None
        assert len(dag.reference_steps) > 0

    def test_dag_has_declared_variables(self, ingester):
        all_ids = list(ingester.catalog.keys())
        dag = ingester.build_problem_dag(all_ids[0])
        assert dag is not None
        assert len(dag.declared_variables) > 0

    def test_build_all_dags(self, ingester):
        dags = ingester.build_all_dags()
        assert len(dags) > 0

    def test_nonexistent_family_returns_none(self, ingester):
        dag = ingester.build_problem_dag("NONEXISTENT_FAMILY_ID")
        assert dag is None


@pytest.mark.skipif(not HAS_DATA, reason="BCS dataset files not available")
class TestBenchmarkDataset:
    """Test building BenchmarkDatasetSchema from loaded data."""

    @pytest.fixture
    def ingester(self):
        ing = BCSDatasetIngester(data_dir=DATA_DIR)
        ing.load_all()
        return ing

    def test_build_benchmark_dataset(self, ingester):
        dataset = ingester.build_benchmark_dataset(split="dev")
        assert dataset.split == "dev"
        assert len(dataset.families) > 0

    def test_families_have_attempt_histories(self, ingester):
        dataset = ingester.build_benchmark_dataset(split="dev")
        for family in dataset.families[:5]:
            assert len(family.attempt_histories) > 0, \
                f"Family {family.family_id} has no attempt histories"

    def test_attempt_histories_have_events(self, ingester):
        dataset = ingester.build_benchmark_dataset(split="dev")
        for family in dataset.families[:5]:
            for history in family.attempt_histories:
                assert len(history.events) > 0, \
                    f"History {history.history_id} has no events"

    def test_limited_families(self, ingester):
        all_ids = list(ingester.catalog.keys())[:5]
        dataset = ingester.build_benchmark_dataset(split="pilot", family_ids=all_ids)
        assert len(dataset.families) == len(all_ids)
