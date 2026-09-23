"""Run comparative evaluation of Baselines B0-B3 and GonitSathi (G).

Usage:
    python scripts/run_comparative_eval.py [--max-families N] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.baselines.b0_rule_template import RuleTemplateTutor
from src.baselines.b1_prompted import PromptedTutor
from src.baselines.b2_verify_then_generate import VerifyThenGenerateTutor
from src.baselines.b3_bayesian import BayesianDiagnosticTutor
from src.baselines.b4_intellicode import IntelliCodeTutor
from src.baselines.b5_scaffoldlm import ScaffoldLMTutor
from src.baselines.b6_slow import SlowWorkspaceTutor
from src.baselines.gonitsathi_adapter import GonitSathiTutor
from src.benchmark.dataset_ingester import BCSDatasetIngester
from src.evaluation.comparative_harness import ComparativeHarness


def main():
    parser = argparse.ArgumentParser(description="Run comparative evaluation across B0-B6 and G")
    parser.add_argument("--split", type=str, default="dev", choices=["dev", "test", "train", "all"], help="Benchmark split to evaluate")
    parser.add_argument("--use-manifest", action="store_true", default=True, help="Use manifest-based splits")
    parser.add_argument("--max-families", type=int, default=None, help="Number of families to evaluate (default: all in split)")
    parser.add_argument("--output-dir", type=str, default="evaluations/comparative", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("GonitSathi Comparative Evaluation: Baselines B0-B6 vs GonitSathi (G)")
    print(f"Benchmark Split: {args.split} (use_manifest={args.use_manifest}, max_families={args.max_families})")
    print("=" * 80)

    # Ingest data
    ingester = BCSDatasetIngester()
    ingester.load_all()
    dataset = ingester.build_benchmark_dataset(split=args.split, use_manifest=args.use_manifest)

    systems = [
        RuleTemplateTutor(),
        PromptedTutor(),
        VerifyThenGenerateTutor(),
        BayesianDiagnosticTutor(activation_threshold=0.80),
        IntelliCodeTutor(),
        ScaffoldLMTutor(),
        SlowWorkspaceTutor(),
        GonitSathiTutor(activation_threshold=0.80),
    ]

    harness = ComparativeHarness()
    reports = {}

    target_count = args.max_families if args.max_families is not None else len(dataset.families)
    print(f"\nEvaluating {len(systems)} architectures on {target_count} families from '{args.split}' split...\n")

    for system in systems:
        print(f"--> Running {system.name}...")
        report = harness.evaluate_tutor(
            tutor=system,
            dataset=dataset,
            ingester=ingester,
            max_families=args.max_families,
        )
        reports[system.name] = report.to_dict()

        # Display concise summary
        m = report.metrics
        r = report.resource_stats
        r_risk = f"{m.get('unsupported_commit_risk', 0.0) * 100:.1f}%" if isinstance(m.get('unsupported_commit_risk'), (int, float)) else str(m.get('unsupported_commit_risk'))
        c_cov = f"{m.get('commitment_coverage', 0.0) * 100:.1f}%" if isinstance(m.get('commitment_coverage'), (int, float)) else str(m.get('commitment_coverage'))
        brier = f"{m.get('multiclass_brier_score'):.3f}" if isinstance(m.get('multiclass_brier_score'), (int, float)) else str(m.get('multiclass_brier_score'))
        a_fe = f"{m.get('first_error_accuracy', 0.0) * 100:.1f}%" if isinstance(m.get('first_error_accuracy'), (int, float)) else str(m.get('first_error_accuracy'))
        lat = f"{r.get('avg_latency_ms', 0.0):.2f} ms"
        print(f"    R_commit: {r_risk} | C_commit: {c_cov} | Brier: {brier} | A_FE: {a_fe} | Latency: {lat}")

    # Save summary table JSON
    summary_path = out_dir / "comparative_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

    split_path = out_dir / f"comparative_summary_{args.split}.json"
    with open(split_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Full comparative evaluation results saved to:\n  - {summary_path}\n  - {split_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
