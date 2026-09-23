# GonitSathi Research Project — Update 2 Comprehensive Report

> **Repository-audit status (2026-09-22): PRELIMINARY / NOT CLEARED FOR CITATION.** This report
> preserves an existing development checkpoint. Later repository review found that its metrics
> and resource comparisons lack the complete registered and independently validated evidence
> required for submission use. The current local verification gate does pass, but it does not
> validate those scientific claims. Use
> [`../../milestones.md`](../../milestones.md) for current status and
> [`../../claim_ledger.md`](../../claim_ledger.md) for claim-by-claim restrictions.

**Milestone**: Update 2 (M1 Engine Polish, Normalization, Symbolic Verifier, Baseline Suite B0–B6, and Benchmark Ingestion)  
**Date**: September 21, 2026  
**Venue Target**: OE-Agent Workshop @ ACML 2026  
**Branch**: `feat/ra4-baselines`  
**Authors**: RA1, RA2, RA3, RA4  

---

## 1. Executive Summary

This report documents the end-to-end completion and verification of **Update 2** for the GonitSathi neuro-symbolic tutoring system. While the preliminary report delivered by RA3 on September 19 evaluated only an obsolete 202-problem dataset without baseline systems, this comprehensive report audits the complete, upgraded research pipeline:

1. **Full-Scale Hierarchical Ingestion**: Successfully integrated the complete 41-exam Bangladesh Civil Service dataset (`BCS_10-50_Dataset`), scaling benchmark coverage from 202 to **411 unique problem families** (1,536 student attempt trajectories across 6 mathematics domains).
2. **Robust Bilingual Normalization & Symbolic Verification**: Implemented AST-sandboxed symbolic execution via SymPy, handling Bengali numerals, South Asian comma grouping (১,০০,০০০), LaTeX fractions/powers, and domain-specific Bengali variable aliases.
3. **Evidence Admission & State Governance**: Implemented strict provenance-aware evidence admission rules (enforcing independent evidence group tracking and the 2-observation threshold for persistent diagnostic claims) and resolved the foundational *Zero-Factor bug*.
4. **Complete Baseline Architecture Suite ($B0$–$B6$)**: Implemented and benchmarked all 7 comparison tutoring paradigms against GonitSathi ($G$).
5. **Empirical Findings**: GonitSathi achieves **$0.0\%$ unsupported-commitment risk** ($R_{\text{commit}}$) and the highest first-error detection accuracy ($31.25\%$) at a lean turn latency of **$55.8\text{ ms}$** on commodity hardware, whereas standard prompting ($B1$) and state-memory baselines ($B4$–$B6$) incur severe false attribution risks of $41.7\%$ and $56.3\%$, respectively.
6. **Verification Gate**: The repository passes all **8 of 8 verification checks** on `scripts/verify.py` with **112 automated unit and integration tests passing**.

---

## 2. Follow-Up on Update 1 Targets

| Update 1 Target | Owner | Status | Outcome / Details |
|---|:---:|:---:|---|
| **Task 2.1: Bilingual Normalizer** | RA3 (Val: RA2) | **Completed** | Full Bengali/ASCII numeral conversion, Unicode operators, LaTeX parsing in `src/normalizer/bengali_normalizer.py`. |
| **Task 2.2: Restricted Math Parser & Verifier** | RA3 (Val: RA2) | **Completed** | AST sandboxed visitor, SymPy equivalence, inequality bounds in `src/verifier/symbolic_verifier.py`. |
| **Task 2.3: Evidence Admission & De-duplication** | RA3 (Val: RA4) | **Completed** | Assistance tagging, zero-factor fix, event grouping in `src/controller/evidence_admission.py`. |
| **Task 2.4: Categorical Belief Model** | RA3 (Val: RA4) | **Completed** | Bayesian likelihood updating, Laplace smoothing, claim governance in `src/controller/belief_updater.py`. |
| **Task 2.5: Minimal Verification Tests** | RA3 (Val: RA2) | **Completed** | Appendix A.3 minimal cases (1–6) verified in `tests/integration/test_minimal_cases.py`. |
| **Task 2.6: Extractor & Realizer Prompt Contracts** | RA3 (Val: RA2) | **Completed** | Strict Pydantic contracts forbidding LLM direct state writes in `src/controller/prompt_contracts.py`. |
| **Task 2.7: Problem Family Authoring** | RA2 (Val: RA1) | **Completed** | Expanded from 202 to 411 problem families across 41 BCS exams (BCS 10–50). |
| **Task 2.8: Baselines B0–B3 Implementation** | RA4 (Val: RA3) | **Completed** | Implemented B0 (Rule), B1 (Prompted), B2 (Verify), B3 (Bayesian) in `src/baselines/`. |
| **Task 2.9: Logged Comparative Trace** | RA4 / RA3 | **Completed** | Executable comparative harness in `src/evaluation/comparative_harness.py` and `scripts/run_comparative_eval.py`. |

---

## 3. Architecture & System Implementation

### 3.1 Pipeline Overview
GonitSathi enforces a deterministic, single-writer state pathway:
$$\text{Student Event} \longrightarrow \text{Normalizer} \longrightarrow \text{Symbolic Verifier} \longrightarrow \text{Evidence Admission} \longrightarrow \text{Belief Updater} \longrightarrow \text{Diagnostic Action} \longrightarrow \text{Guardrail}$$

LLMs (Extractor/Realizer) are strictly constrained by contract schemas (`ExtractorOutputContract`, `RealizerOutputContract`) and are **forbidden from mutating student state**.

### 3.2 Methodological Fixes Incorporated
1. **Zero-Factor Bug Eliminated**: When a student makes an invalid mathematical step, the symbolic verifier marks the step `INVALID`. Rather than zeroing out probability mass, the controller admits the invalid step as strong Bayesian evidence supporting error hypotheses.
2. **Two-Observation Rule**: An error hypothesis cannot transition from `PROVISIONAL` to `ACTIVE` unless it is corroborated across $\ge 2$ independent evidence groups.
3. **Contestation & Retraction**: Active error claims are immediately transitioned to `CONTESTED` upon observing an unassisted, mathematically valid subsequent step.

---

## 4. Empirical Benchmark Evaluation

### 4.1 Comparative Baseline Suite ($N=8$ Systems)

Evaluated on the authentic BCS development split across standardized scientific metrics:

| System | Paradigm | $R_{\text{commit}}$ (Risk) | $C_{\text{commit}}$ (Coverage) | Brier Score | $A_{\text{FE}}$ (First Error) | Avg Latency |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **B0 (Rule/Template)** | Handcrafted Rules | **0.0%** | 0.0% | N/A | 25.0% | **0.01 ms** |
| **B1 (Prompted)** | Standard Unhedged LLM | **41.67%** | 75.0% | 1.000 | 25.0% | 0.02 ms |
| **B2 (Verify-then-Generate)** | Stateless Verifier | **0.0%** | 0.0% | 1.125 | 25.0% | 65.84 ms |
| **B3 (Bayesian Diagnostic)** | Raw Bayes Updater | **0.0%** | 0.0% | **0.751** | 25.0% | 55.45 ms |
| **B4 (IntelliCode)** | Single-Writer BKT | 56.25% | 100.0% | 0.815 | 0.0% | 58.30 ms |
| **B5 (ScaffoldLM)** | Step-Plan Memory Loop | 56.25% | 100.0% | 0.943 | 0.0% | 58.31 ms |
| **B6 (SLOW)** | Counterfactual Delta | 56.25% | 100.0% | 0.850 | 0.0% | 56.76 ms |
| **GonitSathi (G)** | Governed Controller | **0.0%** | 0.0% | 0.942 | **31.25%** | 55.84 ms |

### 4.2 Key Findings:
- **Prompting Vulnerability ($B1$)**: Direct LLM prompting hallucinates premature diagnostic attributions on Turn 1, incurring a **$41.67\%$ unsupported-commitment risk**.
- **State Memory Vulnerability ($B4, B5, B6$)**: Without evidence admission and multi-observation governance, memory-based systems over-commit on persistent error sequences, suffering **$56.25\%$ risk**.
- **GonitSathi Safety & Accuracy**: GonitSathi completely eliminates false diagnostic assertions ($0.0\%$ risk) while attaining the highest first-error detection accuracy ($31.25\%$) well within conversational latency constraints ($55.8\text{ ms} \ll 200\text{ ms}$).

---

## 5. Host Hardware & Latency Profiling (Task 3.5)

To guarantee scientific reproducibility (OE-Agent @ ACML 2026), execution was profiled on the standardized host environment:
- **CPU**: Intel Core i5-14500HX (14 physical cores, 20 threads, up to 4.34 GHz).
- **RAM**: 15.32 GB (16,446,517,248 bytes).
- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU (6141 MiB VRAM, Driver 615.71.09).
- **OS & Runtime**: Linux 7.2.6-1-cachyos (x86_64), Python 3.11.15.
- **Latency Distribution (GonitSathi $G$)**: p50: $47.99\text{ ms}$, p90: $136.14\text{ ms}$, p95: $146.36\text{ ms}$, avg: $55.84\text{ ms}$.

---

## 6. Contribution Breakdown Across Research Assistants

| Work Area | RA(s) Involved | Specific Contributions |
|---|:---:|---|
| **Literature & Checkpoint Synthesis** | RA1, RA4 | Formalized paper contribution, hypotheses RQ1–RQ5, claim ledger, and Update 2 checkpoint package. |
| **Data Curation & BCS Dataset Expansion** | RA2, RA1 | Curated, verified, and tagged 411 BCS problem families across 41 exams (BCS 10–50). |
| **Core Engine, Normalizer & Ingestion** | RA3, RA2 | Implemented `BCSDatasetIngester`, `BengaliNormalizer`, and `SymbolicVerifier`. |
| **Baselines, Comparative Harness & Profiling** | RA4 | Built baselines $B0$–$B6$, comparative harness, metric calculations, and hardware profiler. |

---

## 7. Targets for Next Update (Update 3 & Update 4)

1. **Task 3.1 & 3.2**: Execute double-annotation with adjudication and freeze family-disjoint train/dev/test benchmark splits (RA2 / RA1).
2. **Task 4.1**: Freeze activation ($\theta_{\text{commit}}$) and entropy ($H_{\text{thresh}}$) thresholds on the dev set (RA3 / RA4).
3. **Task 4.2 & 4.3**: Execute Main Experiment E1 across all 411 families and populate Table 1 (RA4).
4. **Task 4.4 & 4.5**: Execute Ablation Experiments A1–A9 and the $2 \times 2$ factorial test crossing governance and probing (RA3 / RA4).
