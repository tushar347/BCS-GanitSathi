"""Evaluate BCS math datasets through the GonitSathi diagnostic controller.

Usage:
    python scripts/evaluate_bcs_dataset.py [--data-dir DATA_DIR] [--max-families N] [--output-dir DIR]

Loads RA2's raw BCS JSON datasets, runs them through the full pipeline,
and outputs evaluation metrics, latency profiles, and per-family results.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path and stdout handles UTF-8
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.evaluation.harness import EvaluationHarness


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate BCS math datasets through GonitSathi diagnostic controller"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw_bcs",
        help="Path to directory containing BCS JSON files",
    )
    parser.add_argument(
        "--max-families",
        type=int,
        default=None,
        help="Maximum number of families to evaluate (for quick testing)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluations/logs",
        help="Directory to write evaluation results",
    )
    parser.add_argument(
        "--activation-threshold",
        type=float,
        default=0.80,
        help="Belief activation threshold for claim promotion",
    )
    parser.add_argument(
        "--retention-threshold",
        type=float,
        default=0.40,
        help="Belief retention threshold before claim retraction",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="all",
        choices=["train", "dev", "test", "pilot", "all"],
        help="Dataset split label ('all', 'train', 'dev', 'test', 'pilot')",
    )
    parser.add_argument(
        "--use-manifest",
        action="store_true",
        default=True,
        help="Use frozen train/dev/test split manifest if available",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GonitSathi BCS Math Dataset Evaluation (411 Problem Families)")
    print("=" * 70)

    # 1. Ingest datasets
    print(f"\n[1/4] Loading datasets from: {data_dir.resolve()}")
    ingester = BCSDatasetIngester(data_dir=data_dir)
    counts = ingester.load_all()
    summary = ingester.get_summary()
    print(f"  Loaded: {counts}")
    print(f"  Topics: {summary['topics']}")

    # 2. Build benchmark dataset
    print(f"\n[2/4] Building benchmark dataset (split={args.split}, use_manifest={args.use_manifest})...")
    dataset = ingester.build_benchmark_dataset(split=args.split, use_manifest=args.use_manifest)
    print(f"  Total families: {len(dataset.families)}")

    if not dataset.families:
        print("\n  ERROR: No families found in dataset. Check data files.")
        sys.exit(1)

    # 3. Run evaluation
    print("\n[3/4] Running evaluation pipeline...")
    if args.max_families:
        print(f"  (Limited to {args.max_families} families)")

    harness = EvaluationHarness(
        activation_threshold=args.activation_threshold,
        retention_threshold=args.retention_threshold,
    )
    report = harness.evaluate_dataset(
        dataset=dataset,
        ingester=ingester,
        max_families=args.max_families,
    )

    # 4. Display results
    print("\n[4/4] Evaluation Results")
    print("-" * 50)
    print(f"  Split: {report.split}")
    print(f"  Families evaluated: {report.total_families}")
    print(f"  Histories evaluated: {report.total_histories_run}")

    print("\n  Aggregate Metrics:")
    for metric_name, metric_value in report.aggregate_metrics.items():
        print(f"    {metric_name}: {metric_value}")

    print("\n  Latency Summary:")
    latency = report.latency_summary
    if "total_latency" in latency:
        tl = latency["total_latency"]
        print(f"    Avg per-step: {tl['avg_ms']:.2f} ms")
        print(f"    Max per-step: {tl['max_ms']:.2f} ms")
        print(f"    Min per-step: {tl['min_ms']:.2f} ms")
        print(f"    P95 per-step: {tl['p95_ms']:.2f} ms")
    if "per_stage" in latency:
        print("    Per-stage breakdown:")
        for stage, stats in latency["per_stage"].items():
            print(f"      {stage}: avg={stats['avg_ms']:.2f}ms, max={stats['max_ms']:.2f}ms")

    print("\n  Per-Topic Summary:")
    for topic, stats in report.per_topic_summary.items():
        print(f"    {topic}: total={stats['total']}, correct={stats['correct']}, errors={stats['errors']}")

    # Save full report
    report_path = output_dir / f"bcs_eval_{args.split}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"\n  Full report saved to: {report_path.resolve()}")

    # Save latency profile
    latency_path = output_dir / f"latency_profile_{args.split}.json"
    with open(latency_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": report.latency_summary,
            "per_step": harness.profiler.get_per_step_report(),
        }, f, indent=2)
    print(f"  Latency profile saved to: {latency_path.resolve()}")

    print("\n" + "=" * 70)
    print("Evaluation complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
