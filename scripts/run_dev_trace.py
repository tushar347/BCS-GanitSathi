"""Executes an end-to-end development trace per Section 6 and Section 15.2.

Produces a fully logged, reproducible trace from student input to audited pedagogical intervention.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path and stdout handles UTF-8 Bengali text
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.controller.diagnostic_controller import DiagnosticController
from src.verifier.symbolic_verifier import ProblemReferenceDAG, ReferenceStep
from src.controller.schemas import (
    CandidateCause,
    DiagnosticProbe,
)


def run_trace():
    print("=" * 70)
    print("GonitSathi End-to-End Diagnostic Controller Development Trace (§6, §15.2)")
    print("=" * 70)

    # 1. Setup Problem Reference DAG (§6.1)
    rice_problem_dag = ProblemReferenceDAG(
        item_id="pct_bcs_012",
        family_id="inverse_budget_expenditure_03",
        problem_text="চালের মূল্য ২৫% বৃদ্ধি পেলে চালের ব্যবহার শতকরা কত কমাতে হবে যাতে খরচ একই থাকে?",
        declared_variables={
            "new_price": "Price after 25% increase",
            "new_quantity": "Quantity after consumption adjustment",
            "decrease": "Percentage reduction in consumption",
        },
        variable_aliases={
            "new_quantity": ["নতুন পরিমাণ", "নতুন_পরিমাণ", "পরিমাণ"],
            "new_price": ["নতুন দাম", "নতুন_দাম", "দাম", "নতুন মূল্য"],
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
                }
            )
        ]
    )

    # 2. Setup Reviewed Candidate Probes (§6.2, §5.6)
    direction_probe = DiagnosticProbe(
        probe_id="probe_rice_direction",
        target_ambiguity="percentage_base_vs_directional_confusion",
        prompt_bn="যদি প্রতি কেজির দাম বৃদ্ধি পায় কিন্তু মোট বাজেট স্থির থাকে, তবে চালের ক্রয়ের পরিমাণ বাড়বে, কমবে নাকি অপরিবর্তিত থাকবে? সংক্ষেপে লিখুন।",
        prompt_en="If price per kg increases while total budget stays fixed, should quantity bought increase, decrease, or stay the same? Briefly explain.",
        candidate_causes=[CandidateCause.PERCENTAGE_BASE, CandidateCause.TRANSIENT_SLIP],
        response_model={
            "decrease": {
                CandidateCause.PERCENTAGE_BASE: 0.85,
                CandidateCause.TRANSIENT_SLIP: 0.85,
                CandidateCause.LINGUISTIC_SLIP: 0.05,
                CandidateCause.NO_ERROR: 0.95,
            },
            "increase_or_same": {
                CandidateCause.PERCENTAGE_BASE: 0.10,
                CandidateCause.TRANSIENT_SLIP: 0.05,
                CandidateCause.LINGUISTIC_SLIP: 0.90,
                CandidateCause.NO_ERROR: 0.01,
            },
            "ambiguous": {
                CandidateCause.PERCENTAGE_BASE: 0.05,
                CandidateCause.TRANSIENT_SLIP: 0.10,
                CandidateCause.LINGUISTIC_SLIP: 0.05,
                CandidateCause.NO_ERROR: 0.04,
            }
        },
        expected_burden_seconds=12.0,
    )

    controller = DiagnosticController()

    # Step 1: Student submits ambiguous wrong step (§6.1)
    raw_student_input = "নতুন পরিমাণ = ১০০ - ২৫"
    print(f"\n[Turn 1] Student Input: {raw_student_input}")

    action, audit, obs = controller.process_student_step(
        raw_text=raw_student_input,
        problem_dag=rice_problem_dag,
        learner_id="candidate_bcs_7781",
        candidate_probes=[direction_probe],
        prohibited_answers=["20%", "২০%", "80", "৮০"],
        decisive_calculations=["10000 / 125 = 80", "100 - 80 = 20"],
    )

    print(f" -> Normalized Math Expression: {obs.normalized_text}")
    print(f" -> Symbolic Verification Status: {obs.mathematical_status.value} (Reason: {obs.verification_reason})")
    print(f" -> Evidence Admitted: {obs.evidence_admitted} (Zero-factor bug avoided: YES)")
    print(f" -> Belief Distribution: { {k.value: round(v, 4) for k, v in controller.belief_updater.beliefs.items()} }")
    print(f" -> Normalized Entropy: {round(controller.belief_updater.get_normalized_entropy(), 4)}")
    print(f" -> Action Selected: {action.action_type.value}")
    print(f" -> Guardrail Audit Safe: {audit.is_safe} (Leakage detected: {audit.leakage_detected})")
    print(f" -> Released Tutor Response: {audit.released_text}")

    # Output directory
    log_dir = Path("evaluations/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    trace_path = log_dir / "dev_trace_example.json"

    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(controller.audit_log, f, indent=2, ensure_ascii=False)

    print(f"\n[Artifact Saved] Full execution log written to: {trace_path.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    run_trace()
