# GonitSathi Documentation Index

This directory contains the governance, architectural specifications, empirical evaluation reports, and historical audits for the **GonitSathi** research project (Target: OE-Agent Workshop @ ACML 2026).

> **Status note (2026-09-22):** [`milestones.md`](milestones.md) is the current operational
> source of truth. Update 2/3 reports preserve preliminary development results and must not be
> treated as verified experiment evidence. See [`claim_ledger.md`](claim_ledger.md) for the
> quarantined claims and their release conditions.

---

## Directory Organization

```text
docs/
├── README.md                           # This index file
├── claim_ledger.md                     # Central scientific claim ledger and hypothesis bounds
├── sprint_backlog.md                   # Phased sprint timeline and task progress
├── milestones.md                       # Milestone governance & status verification rules
├── methodology/                        # Research design, fixes, specs, and literature positioning
│   ├── methodological_fixes.md         # Eight mandatory methodological corrections
│   ├── baseline_differences.md         # Baseline architectures (B0–B6) paradigm comparison
│   ├── hardware_and_profiling_spec.md  # Standardized host hardware and latency measurement spec
│   └── literature_matrix.md            # Structured R1–R18 literature comparison matrix
├── reports/                            # Milestone submission checkpoints and manuals
│   ├── GS_Main_Guide.pdf               # Primary research and RA execution manual
│   ├── GonitSathi_Research_Report_v2.pdf # Foundational research synthesis
│   ├── update_1/                       # Update 1 (13 Sept 2026) checkpoint report
│   │   └── supervisor_checkpoint_update_1.md
│   ├── update_2/                       # Update 2 (21 Sept 2026) checkpoint report & artifacts
│   │   ├── update_2_report.pdf         # Publication-grade IEEE report for supervisor review
│   │   ├── update_2_report.tex         # LaTeX source for Update 2 report
│   │   ├── update_2_comprehensive_report.md # Markdown comprehensive report
│   │   ├── RA3_Update_2_Report.pdf     # Engineering update report
│   │   ├── eval_metrics_summary.png    # High-resolution benchmark visualization
│   │   └── IEEEtran.cls                # IEEE LaTeX template class
│   └── update_3/                       # Update 3 (23 Sept 2026) checkpoint report & 411 benchmark
│       ├── RA3_Update_3_Report.pdf     # Publication-grade supervisor checkpoint report
│       ├── update_3_report.pdf         # Checkpoint report alias
│       ├── update_3_comprehensive_report.md # Markdown comprehensive report with full findings
│       └── report_assets/              # High-resolution benchmark charts and figures
├── audits/                             # Historical verification, ingestion logs, and session work logs
│   ├── task_1_3_methodological_fixes_audit.md
│   ├── task_1_7_schema_audit.md
│   ├── ra4_baseline_work_log.md
│   ├── dataset_ingestion_audit_log.md
│   ├── pilot_28_cross_check_audit.md
│   └── session_work_log_update2.md
├── rubrics/                            # Evaluation and annotation rubrics
│   └── expert_rubric.md                # 3-point anchored human expert scoring rubric
└── figures/                            # Publication and presentation charts
    └── eval_metrics_summary.png        # Benchmark metrics chart (Commitment Risk vs. Latency)
```

---

## Quick Reference Links
* **Main Manual:** [`reports/GS_Main_Guide.pdf`](reports/GS_Main_Guide.pdf)
* **Current Milestone Status:** [`milestones.md`](milestones.md)
* **Detailed Sprint Roadmap:** [`sprint_backlog.md`](sprint_backlog.md)
* **Scientific Claim Boundary:** [`claim_ledger.md`](claim_ledger.md)
* **Latest Preliminary Supervisor Report:** [`reports/update_3/update_3_comprehensive_report.md`](reports/update_3/update_3_comprehensive_report.md)
* **Methodological Corrections:** [`methodology/methodological_fixes.md`](methodology/methodological_fixes.md)

## Agentic AI runtime

- [`agentic_ai_architecture.md`](agentic_ai_architecture.md): complete runtime architecture, permissions, cycle and local-model integration.
- [`mentor_learning_material.md`](mentor_learning_material.md): simple explanation, example, viva answer and mentor Q&A.
