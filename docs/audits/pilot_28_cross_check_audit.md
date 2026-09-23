# Scientific Integrity & Dataset Cross-Check Audit Report

**Date:** 18 September 2026  
**Auditor:** GonitSathi Research Team  
**Audit Target:** 28-Family Pilot Benchmark ([`data/benchmark/pilot/pilot_28_families.json`](file:///data/rspace/codespace/projects/GonitSathi/data/benchmark/pilot/pilot_28_families.json))  
**Curated Catalog:** [`data/raw_bcs/bcs_math_catalog.json`](file:///data/rspace/codespace/projects/GonitSathi/data/raw_bcs/bcs_math_catalog.json)  
**Branch:** `dataset`  
**Latest Audit Commit:** `ee6eae9`

---

## 1. Executive Summary

This cross-check audit was conducted to verify scientific integrity, mathematical authenticity, and protocol conformance across our initial 28-family pilot benchmark. 

The audit identified an initial defect where questions containing exam typos or disclaimers had been inadvertently included. This defect has been resolved: all 28 families are now verified, strictly clean, authentic past BCS examination problems with comprehensive multi-step mathematical derivations.

---

## 2. Issues Discovered During Initial Ingestion & How They Were Fixed

| Component | Defect Found in Initial Sweep | Remediation & Fix Applied | Integrity Status |
| :--- | :--- | :--- | :---: |
| **Exam Printing Typos** | In the raw files, questions `Q0004` and `Q0005` contained notes acknowledging printing mistakes in the original examination questions (`"মুদ্রণগত অসঙ্গতি"`, `"অস্পষ্টতা"`). | Programmatic filtering now excludes any raw BCS question that has disclaimer flags. All 28 selected pilot families have clean, unambiguous derivations. | **PASS** |
| **Formula-less Placeholders** | Some raw items in `Downloads` had placeholders instead of step-by-step math (e.g. `"একটি distractor option"`). | Filtered the catalog to guarantee every family has $\ge 3$ verified mathematical solution steps and 4 distinct multiple-choice options. | **PASS** |
| **Trajectory Realism** | Initial trajectory generator used static generic strings for `H2` and `H3`. | Updated [`scripts/generate_pilot_dataset.py`](file:///data/rspace/codespace/projects/GonitSathi/scripts/generate_pilot_dataset.py) to anchor `H1` directly on the exam's verified multi-step derivation, `H2` on the authentic distractor, and `H3` on terminal arithmetic evaluation divergence. | **PASS** |

---

## 3. Topic Distribution & Quota Balance (28 Families)

The 28 pilot families are distributed across the core curriculum domains:

| Curriculum Domain | Target Quota | Verified Families Ingested | Evaluated Trajectories ($N \times 4$) |
| :--- | :---: | :---: | :---: |
| **Algebra** | 6 | 6 | 24 |
| **Arithmetic** | 6 | 6 | 24 |
| **Geometry** | 5 | 5 | 20 |
| **Percentages / Profit & Loss** | 4 | 4 | 16 |
| **Ratios & Proportions** | 4 | 4 | 16 |
| **Mensuration** | 3 | 3 | 12 |
| **Total** | **28** | **28** | **112** |

---

## 4. Verification of the 4 Trajectory Schemas (§7.2, §5.6)

Every family was inspected to ensure it complies with the four-history schema without data contamination:

1. **`H1_CORRECT` (Valid Multi-Step Derivation)**:
   * Contains the complete step sequence from the authentic BCS solution.
   * `mathematical_status`: `valid`
   * `gold_error_cause`: `no_error`
2. **`H2_CONCEPTUAL` (Persistent Conceptual Error)**:
   * Misapplies a structural relation, leading directly to an authentic distractor option from the exam paper.
   * `mathematical_status`: `invalid`
   * `gold_error_cause`: `percentage_base` (for percentage problems) or `unresolved` (awaiting probe/adjudication).
3. **`H3_SLIP` (Transient Arithmetic Slip)**:
   * Preserves the correct intermediate algebraic setup, but introduces a careless arithmetic calculation error at the final evaluation step.
   * `mathematical_status`: `invalid`
   * `gold_error_cause`: `transient_slip`
4. **`H4_AMBIGUOUS` (Incomplete / Ambiguous Attempt)**:
   * Gives only the first valid setup step, requiring information-seeking intervention.
   * `mathematical_status`: `unsupported`
   * `gold_error_cause`: `unresolved`
   * **Diagnostic Probe Included**: Each `H4` trajectory includes an explicit probe question in both Bengali and English (`prompt_bn`, `prompt_en`) targeting the student's next step.

---

## 5. Adherence to Faculty Invariants & Research Ethics

* **Zero Hallucination of Student Data**: No fake student interaction logs or scraped private information were used. Trajectories are mathematically derived directly from the official exam keys and distractors.
* **Family Disjointness**: All 28 families have unique, immutable identifiers (`FAM_<TOPIC>_<EXAM>_<INDEX>`).
* **Ready for Inter-Rater Reliability (Task 1.8)**: This dataset provides the exact corpus needed for RA1 and RA2 to conduct double-blind scoring and measure Cohen's $\kappa$.
