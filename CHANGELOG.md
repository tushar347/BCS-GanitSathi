# Changelog

All notable changes to the GonitSathi project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.2.0-rc] — 2026-09-13

### Summary
**RA 3 (Methods, Logic & Controller Engineer)** — Core diagnostic engine implementation,
evaluation metrics framework, and CI pipeline stabilization for Sprint Update 2.

### Added

#### Core Diagnostic Pipeline (§5.1–5.7, Appendix A.2)
- `src/controller/diagnostic_controller.py` — Main pipeline orchestrator coordinating
  normalization → verification → admission → belief update → probe selection → guardrail.
- `src/controller/schemas.py` — Pydantic data models: `Observation`, `HypothesisRecord`,
  `PedagogicalAction`, `DiagnosticProbe`, `CandidateCause`, `ClaimStatus`, enums.
- `src/controller/belief_updater.py` — Calibrated Bayesian categorical belief distribution
  tracker with zero-factor bug fix (§5.4).
- `src/controller/evidence_admission.py` — Evidence admission manager enforcing independent
  evidence grouping and assistance provenance tagging (§5.3).
- `src/controller/probe_selector.py` — Expected Information Gain (EIG) probe selector with
  strict N_probe ≤ 1 per episode constraint (§5.5).
- `src/controller/guardrail.py` — Answer-leakage prevention and pedagogical fallback
  generator with audit trail (§5.6).
- `src/controller/prompt_contracts.py` — Prompt contract schemas for LLM extractor/realizer.

#### Bengali Normalizer (§5.2)
- `src/normalizer/bengali_normalizer.py` — Reversible Bengali↔ASCII numeral conversion,
  operator standardization (×→*, ÷→/, ≥→>=), unit preservation (টাকা, কেজি, %),
  and character-level alignment mapping.

#### Symbolic Verifier (§5.3)
- `src/verifier/symbolic_verifier.py` — Restricted-AST SymPy verifier with safety whitelist
  blocking arbitrary code execution. Supports variable alias resolution and known error
  pattern matching.

#### Evaluation Metrics Engine (§10.1, §10.2)
- `src/evaluation/metrics.py` — Implements four primary evaluation metrics:
  - Unsupported-commit risk
  - Commitment coverage
  - Multiclass Brier score
  - First-error accuracy

#### Benchmark Loader & Schema Validator (§7.2, §7.3)
- `src/benchmark/loader.py` — Strict Pydantic validation for incoming GonitSathi-Bench
  JSON datasets (`ProblemFamilySchema`, `AttemptHistorySchema`).

#### Scripts
- `scripts/verify.py` — Cross-platform repository verification gate covering runtime,
  dependencies, syntax, configuration/schema generation, imports, Ruff, Git whitespace,
  and pytest.
- `scripts/verify.ps1` — Windows PowerShell entry point for the same gate.
- `scripts/run_dev_trace.py` — End-to-end development trace runner with JSON logging.
- `scripts/tune_thresholds.py` — Activation/entropy threshold grid search harness
  (sweeps 0.70–0.95 × 0.4–0.8, optimizes coverage at ≤5% risk).

#### Tests
- `tests/integration/test_minimal_cases.py` — 5 integration tests implementing
  Appendix A.3 minimal meaningful verification cases.
- `tests/test_normalizer.py` — 4 unit tests for Bengali normalizer.
- `tests/test_verifier.py` — 4 unit tests for symbolic verifier.
- `tests/conftest.py` — Shared pytest fixtures (problem DAGs, probes, controllers,
  Bengali text samples, benchmark dataset structures).

### Fixed
- **Zero-Factor Bug** (§5.4) — Invalid mathematical steps now *increase* the likelihood
  of an error cause instead of collapsing the belief distribution to zero.
- `tests/unit/test_normalizer.py` — Aligned test assertions with actual `BengaliNormalizer`
  API (`normalize()` + `to_bengali()` instead of non-existent `to_ascii_digits()`).

### CI/CD
- `.github/workflows/test_engine.yml` — Added `PYTHONPATH` environment variable for
  correct `src.*` import resolution on GitHub Actions runner.
- `.github/workflows/lint_and_contracts.yml` — Fixed schema import
  (`Observation` instead of `ObservationRecord`), added `sympy` to install step.

---

## [0.1.0] — 2026-09-13

### Added (RA 1 — Lead)
- Repository bootstrap: directory structure, agent contracts, `.python-version`,
  `requirements.txt`, GitHub Actions CI workflows, prompt contracts, threshold configs.
- `README.md` with project overview and contributor guide.
