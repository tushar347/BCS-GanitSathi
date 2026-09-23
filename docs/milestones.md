# GonitSathi Milestone Governance

**Project stage:** Core research prototype<br>
**Last reviewed:** 2026-09-22<br>
**Target internal freeze:** 2026-10-16 (AoE)<br>
**Target final submission:** 2026-10-18 (AoE)

This file is the operational source of truth for project progress. It records what is verified, what is only implemented, what comes next, and the evidence required to close each milestone.

Related records:

- `docs/sprint_backlog.md` — detailed task backlog and original schedule.
- `CHANGELOG.md` — historical implementation record.
- `evaluations/registry/run_manifest.csv` — authoritative registry for experimental results.
- `docs/claim_ledger.md` — boundary between inherited claims and reproduced evidence.

## Status Rules

| Status | Meaning |
| --- | --- |
| **Verified** | Implemented, tested or audited, and independently validated with linked evidence. |
| **Implemented** | Code or documentation exists, but its milestone gate has not yet been fully validated. |
| **In progress** | Active work has started but required outputs are incomplete. |
| **Planned** | Scoped but not started. |
| **Blocked** | Cannot proceed until a named dependency or decision is resolved. |

A task may be marked **Verified** only when:

1. Its acceptance criteria are satisfied.
2. Tests, audit output, dataset manifest, or another reproducible artifact is linked.
3. The named validator is different from the primary implementer.
4. Any measured experiment is registered in `evaluations/registry/run_manifest.csv`.

## Pipeline Reality Map

The repository currently has two connected pipelines:

```text
Runtime:
student event -> normalize -> symbolic verify -> admit evidence -> update belief/claim
              -> select probe or instructional action -> guardrail -> released text

Evaluation:
raw BCS JSON -> recursive ingestion -> generated histories -> split selection
             -> B0-B6/G adapters -> metric aggregation -> artifacts/reports
```

| Stage | What exists now | What keeps it from being verified |
| --- | --- | --- |
| Raw data and ingestion | The recursive ingester scans 41 BCS exam directories and loads 411 unique family IDs; one-event evaluation histories are generated from answers and listed mistakes. | Repository metadata identifies the model-authored annotations as drafts requiring independent human review; production schema enforcement, observed human-attempt evidence, and explicit content hashes remain incomplete. |
| Normalization and verification | Bengali/ASCII normalization and restricted symbolic checking are implemented and tested for supported cases. | Supported-domain accuracy on independently labelled authentic responses has not been established. |
| Evidence and learner state | The active path admits evidence, groups independent observations, updates categorical beliefs, and governs revocable claims. | A superseded controller path remains inconsistent with current schemas/configuration, and the end-to-end path lacks independent trace review. |
| Probing and tutoring response | Expected-information-gain selection, a one-probe cap, response contracts, and Bengali leakage guardrails exist. | Benchmark probes are not connected to evaluation, and probe-response classification/update is missing. |
| Baseline adapters | B0–B6 and GonitSathi share a code-level tutor interface. | B1 defaults to an offline simulator, B6 records a simulated reasoning call as neural, and source-faithful matched execution has not been demonstrated. |
| Evaluation and metrics | Comparative, profiling, and reporting code produces development artifacts. | Family-resolution skips, first-error label mismatch, undefined-risk handling, partial profiles, and absent metric tests invalidate current headline results. |
| Experiment governance | Manifests, reports, a registry schema, and governance documents exist. | The repository does not yet evidence a passing content-leakage check, content hashes, adjudication outputs, frozen protocol inputs, registered runs, or independent validation. |

## Current Snapshot

### Implemented

- [x] Repository structure, Python 3.11 pin, dependency list, and CI workflows.
- [x] Core Pydantic schemas for observations, verification, hypotheses, probes, and actions.
- [x] Reversible Bengali numeral and operator normalizer.
- [x] Restricted-AST/SymPy symbolic verifier with known-error and alternative-form handling.
- [x] Evidence admission with invalid-step integrity and independent evidence grouping.
- [x] Categorical Bayesian belief updater with revocable claim states.
- [x] Expected-information-gain probe selection with a one-probe episode cap.
- [x] Canonical local verification gate for runtime, contracts, imports, static checks, and tests.
- [x] Bengali response leakage guardrail and safe fallbacks.
- [x] Prompt-contract schemas, benchmark loader schema, and core evaluation metrics.
- [x] Development-trace and threshold-tuning script scaffolds.
- [x] Unit and integration test definitions for the normalizer, verifier, admission manager, belief updater, minimal controller cases, baselines, dataset ingestion, and profiling.
- [x] Common `BaseTutor` interface and code-level implementations of B0–B6 plus the GonitSathi adapter.
- [x] Recursive ingestion of 411 unique BCS family identifiers and generated one-event evaluation histories.
- [x] A separate 28-family pilot artifact with four constructed trajectory types per family.
- [x] Train/dev/test ID manifests with declared counts of 207/102/102 families.
- [x] Preliminary comparative and five-family hardware-profiling artifacts.
- [x] Research governance documents, claim ledger, literature matrix, and expert rubric.

These items are classified as **Implemented**, not automatically **Verified**. Verification requires the milestone gates below.

### Known Gaps

- [ ] Resolve or remove the superseded controller path in `admission.py`, `belief_model.py`, and `workspace.py`; compatibility aliases allow imports, but the path still uses obsolete fields, assistance enum members, and probe APIs at runtime.
- [ ] Align `configs/thresholds.yaml` with the active controller defaults and assistance-level enum names.
- [ ] Align JSON prompt contracts with the Pydantic prompt-contract models.
- [ ] Strengthen CI so it validates contract equivalence rather than only parsing JSON/YAML.
- [ ] Decide whether Python 3.10/3.12 support is intentional or whether CI should enforce the documented Python 3.11-only policy.
- [ ] Complete Appendix A.1 production metadata, freeze captured provenance, and enforce schema validation/extra-field policy.
- [x] Add direct tests for evidence admission and belief transitions.
- [ ] Add direct tests for probe scoring and response ingestion, guardrail behavior, exact benchmark counts/splits, evaluation metrics, prompt-contract equivalence, and comparative-harness completeness.
- [ ] Replace the threshold-tuning placeholder loop with real dev-set execution.
- [x] Populate benchmark source data and family-ID split manifests.
- [ ] Produce independently adjudicated gold labels, a passing content-aware contamination check, and explicit dataset/split content hashes. At least one exact question-and-options duplicate currently crosses train and dev.
- [x] Implement code-level baselines B0–B6 behind a common interface.
- [ ] Replace offline stand-ins with protocol-faithful execution, use live model calls where the specified baseline mechanism requires them, and enforce matched visible context, tool access, and resource accounting.
- [ ] Fix comparative evaluation family resolution: the committed dev/test summaries declare 102 families but process only 52/70 one-event histories because unresolved DAGs are silently skipped.
- [ ] Correct first-error scoring so predictions and references use the same step identifier, and report unsupported-commit risk as undefined when no commitments exist instead of `0.0`.
- [ ] Connect benchmark probes to evaluation and implement the missing probe-response classification and belief-update path.
- [ ] Integrate and profile the selected small language-model backbones.
- [ ] Register every experiment. `evaluations/registry/run_manifest.csv` currently contains only its header.
- [ ] Run protocol-frozen experiments, human evaluation, stress tests, and statistical analysis.
- [ ] Regenerate reports and figures from registered outputs rather than hard-coded metric tables.
- [ ] Produce the manuscript and reproducibility package.

### Evidence Boundary for Current Results

The committed Update 2/3 metrics are **preliminary development outputs**, not verified research
results. They must not be used in the manuscript as measured properties of GonitSathi or the
comparison systems until all of the following are true:

1. The comparative harness processes every selected family and fails on unexpected skips.
2. Metric definitions and gold-label mappings pass dedicated tests.
3. Test histories have independent annotation/adjudication evidence.
4. Split contamination checks include content fingerprints, not only distinct family IDs.
5. Thresholds, prompts, dataset hashes, model revisions, seeds, and scoring versions are frozen.
6. The run is recorded in `evaluations/registry/run_manifest.csv` with reproducible outputs.

Specific claims currently quarantined include the reported Brier scores, first-error accuracy,
unsupported-commitment risk, commitment coverage, and comparative latency/token/call tables in
the Update 2 and Update 3 reports. In particular, `0.0%` unsupported-commitment risk with `0.0%`
coverage is not evidence of safe diagnosis; it records that no active commitments were made.

Repository-audit anchors for the recovery work:

- `triangular_number_sequence_f01` is assigned to train and
  `triangular_number_sequence_bcs26_q181_f01` to dev, but their question text, options, and answer
  are identical.
- `comparative_summary_dev.json` and `comparative_summary_test.json` each declare 102 families per
  system while containing only 52 and 70 generated histories, respectively.
- `evaluations/registry/run_manifest.csv` contains only its header, so no quantitative result is
  currently linked to a registered run.

## Milestone Plan

### M0 — Specification and Repository Foundation

**Target:** 2026-09-13  
**Status:** In progress; documentation and pilot artifact implemented, external validation pending<br>
**Owners:** RA1, RA2, RA3  
**Validators:** RA4 and Supervisor

Deliverables:

- [x] Research scope and architectural invariants documented.
- [x] Claim ledger and methodological corrections documented.
- [x] Core controller schemas created.
- [x] Literature matrix and expert evaluation rubric created.
- [x] Generate a 28-family pilot with four constructed trajectory types per family.
- [ ] Complete independent double annotation and adjudication of the pilot.
- [ ] Calibrate the expert rubric using pilot disagreements.
- [x] Assemble the supervisor checkpoint package.
- [ ] Obtain Supervisor feedback and record the decision.

Completion gate:

- Pilot artifacts are available, reviewer disagreements are adjudicated, and supervisor feedback is recorded.

### M1 — Coherent and Tested Core Engine

**Target:** 2026-09-16  
**Status:** In progress; core path implemented, coherence gate open<br>
**Owner:** RA3  
**Validators:** RA2 and RA4

Deliverables:

- [x] Bengali normalizer implemented.
- [x] Restricted symbolic verifier implemented.
- [x] Evidence admission implemented.
- [x] Belief updater and claim transitions implemented.
- [x] Bounded probe selector implemented.
- [x] Pedagogical guardrail implemented.
- [x] Minimal end-to-end controller implemented.
- [ ] Reconcile legacy and active controller modules.
- [ ] Reconcile runtime thresholds and all contract representations.
- [x] Add component tests for evidence admission and belief transitions.
- [ ] Add the remaining probe, guardrail, contract-equivalence, metric, and failure-path tests.
- [ ] Run the full supported-version test matrix and record results.
- [x] Implement an end-to-end development-trace runner.
- [ ] Commit and independently review a generated trace artifact.

Completion gate:

- One canonical controller path exists, configurations agree with runtime behavior, all core tests pass in CI, and an independent validator signs off on the minimal verification cases.

### M2 — Pilot Benchmark and Initial Baselines

**Target:** 2026-09-20  
**Status:** In progress; dataset and baseline code exist, benchmark gate open<br>
**Owners:** RA2 and RA4  
**Validators:** RA1 and RA3

Deliverables:

- [x] Ingest 411 unique BCS family identifiers across the available topic groups.
- [x] Generate a 28-family pilot with four trajectory types per family.
- [ ] Reconcile the conflicting documented pilot targets (20 families in the sprint backlog and 30 in the original M2 plan) with the existing 28-family artifact, then validate its schema against the active benchmark loader.
- [ ] Double-annotate and adjudicate pilot labels.
- [x] Create family-ID-disjoint train/dev/test manifests.
- [ ] Remove content-level cross-split duplicates and add explicit content hashes.
- [x] Implement B0 rule/template baseline.
- [x] Implement B1 prompted baseline with injectable live-call support and an offline default simulator.
- [x] Implement B2 verify-then-generate baseline.
- [x] Implement B3 Bayesian diagnostic baseline.
- [x] Specify and implement heuristic adaptations for B4–B6.
- [x] Document baseline differences and intended matched-resource constraints.
- [ ] Demonstrate protocol-faithful, matched-resource execution, including live models where required.

Completion gate:

- Pilot data passes schema validation and split-leakage checks; B0–B6 run through one common interface with identical visible context and resource accounting.

### M3 — Protocol Freeze and Main Experiments

**Target:** 2026-09-23  
**Status:** In progress; preliminary unregistered outputs exist, protocol gate open<br>
**Owners:** RA3 and RA4  
**Validators:** RA1 and independent cross-checker

Deliverables:

- [ ] Execute threshold tuning on the development split.
- [ ] Freeze thresholds, prompts, model revisions, dataset hashes, and scoring version.
- [x] Produce preliminary offline comparative outputs for B0–B6 and GonitSathi.
- [ ] Fix evaluator completeness and scoring defects, then rerun E1 under the frozen protocol.
- [ ] Run ablations A1–A9.
- [ ] Run the governance × probing factorial experiment.
- [x] Produce preliminary risk, coverage, Brier, first-error, latency, call, and token tables.
- [ ] Validate those metrics and regenerate them from registered, complete runs.

Completion gate:

- Every reported run has a complete registry entry, reproducible output artifact, fixed seed, failure record, and validator approval. Test-set results are generated only after protocol freeze.

### M4 — Human Evaluation, Scaling, and Stress Tests

**Target:** 2026-09-26  
**Status:** In progress; a preliminary five-family profile exists, while the main evaluation gates remain open<br>
**Owners:** RA1, RA2, RA3, RA4  
**Validator:** Supervisor

Deliverables:

- [ ] Complete expert audit on 100 contexts with two raters and adjudication.
- [ ] Measure inter-rater agreement.
- [ ] Run model-scaling experiment E3.
- [ ] Run assistance-contamination and long-history stress tests E4.
- [ ] Run Bengali language and numerical perturbation tests E5.
- [ ] Compute confidence intervals and multiplicity-corrected statistics.
- [x] Complete a preliminary five-family CPU-path hardware and resource profile.
- [ ] Complete protocol-scale latency, RAM, VRAM, model-token, actual-call, and fallback profiling.

Completion gate:

- Human and automated results are reproducible, adjudicated, statistically reported, and tied to immutable registry entries.

### M5 — Manuscript and Reproducibility Release

**Target:** 2026-09-29 for first full package; 2026-10-16 internal freeze  
**Status:** Planned  
**Owner:** RA1, with all RAs contributing  
**Validators:** Supervisor and independent reproducer

Deliverables:

- [ ] Draft the complete anonymous manuscript.
- [ ] Generate final figures and tables directly from registered outputs.
- [ ] Re-audit every quantitative claim against the claim ledger and run registry.
- [ ] Package code, frozen configs, schemas, manifests, prompts, and execution instructions.
- [ ] Complete an independent clean-environment reproduction.
- [ ] Complete scientific, ethical, anonymity, and submission-format checks.

Completion gate:

- An independent reviewer can reproduce the primary table from the release package, and every manuscript claim has an auditable source.

## Immediate Next Work

Work should proceed in this order:

1. Quarantine preliminary Update 2/3 quantitative claims from manuscript use.
2. Fix comparative family resolution, require exact selected/processed counts, and retain failure records.
3. Correct first-error and no-commitment metric semantics with dedicated regression tests.
4. Complete double annotation/adjudication, a passing content-level contamination check, and explicit dataset hashes.
5. Establish one canonical controller path and align runtime configuration and all contract representations.
6. Implement real dev-set threshold tuning and freeze thresholds, prompts, models, data, and scoring.
7. Integrate protocol-faithful baseline execution, including live models where required, and the complete probe-response loop.
8. Register and rerun E1 before any further test-set reporting.
9. Run ablations, factorial, human, scaling, stress, and statistical studies.
10. Generate manuscript tables and figures only from registered outputs.

## Governance Checklist for Every Pull Request

- [ ] The change maps to a milestone deliverable.
- [ ] Architectural invariants remain intact.
- [ ] Tests cover new or changed behavior.
- [ ] Data split boundaries and evaluator-only labels remain protected.
- [ ] Configuration and contract changes are synchronized across representations.
- [ ] No inherited or placeholder number is presented as a measured result.
- [ ] Experimental artifacts include commit, dataset, prompt, model, seed, hardware, and scoring identifiers.
- [ ] The validator is not the sole author of the artifact being approved.
- [ ] `CHANGELOG.md`, this file, and the run registry are updated when applicable.

## Milestone Update Log

| Date | Milestone | Change | Evidence | Owner | Validator |
| --- | --- | --- | --- | --- | --- |
| 2026-09-13 | M0–M1 | Initial milestone governance file created from the current repository state. | Repository snapshot at `main` | Project team | Pending |
| 2026-09-13 | M0 | RA1 completed the Task 1.3 methodological audit with a Conditional Pass and recorded protocol-freeze actions. | `docs/audits/task_1_3_methodological_fixes_audit.md` | RA1 | RA3 response and Supervisor acknowledgement pending |
| 2026-09-13 | M0–M1 | RA1 completed the Task 1.7 Appendix A.1 schema audit with a development-only Conditional Pass; production metadata, immutability, validation, and API reconciliation remain open. | `docs/audits/task_1_7_schema_audit.md` | RA1 | RA2/RA3 response and Supervisor acknowledgement pending |
| 2026-09-13 | M1 | Added and baseline-tested a canonical cross-platform repository verification gate with a PowerShell entry point and documented development dependencies. | `scripts/verify.py`, `scripts/verify.ps1`, `requirements-dev.txt`, `pyproject.toml` | RA1 | Green Python 3.11 run and engineering-owner remediation pending |
| 2026-09-13 | M0 | RA1 finalized the Update 1 supervisor checkpoint package and decision record; external validation and RA2/RA3 evidence attachments remain pending. | `docs/reports/update_1/supervisor_checkpoint_update_1.md` | RA1 | Supervisor decision pending |
| 2026-09-22 | M0–M4 | Reconciled milestone status with the current repository. Recorded implemented baselines/data/profiling artifacts separately from unmet validation gates and quarantined preliminary Update 2/3 metrics. | Repository audit at commit `30289f0`; `evaluations/comparative/`; `evaluations/profiling/`; `data/manifests/`; empty run registry | Documentation audit | Independent validator pending |
| 2026-09-22 | M1 | Reproduced the canonical local verification gate under Python 3.11.16: all 8 checks passed and 112 tests passed. This verifies the implemented gate only, not benchmark or experiment validity. | `.venv/bin/python scripts/verify.py` at commit `30289f0` with documentation-only working-tree changes | Documentation audit | Independent/cross-version validation pending |
