# Baseline Adaptation Differences Table

**Author**: RA4 (Evaluation Lead - `rmia46 <mail.romanmia+github@gmail.com>`)  
**Sprint**: Update 3, Task 3.4  
**Reference**: GonitSathi Guideline §8 (Table 6), §9, §16.2  
**Target Venue**: OE-Agent @ ACML 2026  

---

## 1. Architectural & Methodological Differences Matrix

This document provides the mandatory differences table required by §8 to justify and document adaptations of baseline tutoring architectures (B4–B6) to the bilingual Bengali competitive mathematics benchmark (GonitSathi-Bench).

| System ID | System Name | Original Paper & Reference | Core Mechanism in Source | Adaptation for GonitSathi-Bench | Key Controlled Difference vs GonitSathi ($G$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B0** | **Reviewed Rule / Template Tutor** | Standard ITS Literature | Handcrafted expert production rules | Deterministic keyword matching against reference DAG error patterns | No generative diagnosis; efficiency floor ($0.01\text{ ms}$). |
| **B1** | **Strong Prompted Tutor** | Standard Prompting / Few-Shot LLM | In-context reasoning with task instructions | Structured prompt (Appendix B.1/B.2) providing stem, DAG, and recent history | Single-turn unhedged commitment; lacks evidence admission ($R_{\text{commit}} = 41.7\%$). |
| **B2** | **Verify-then-Generate Tutor** | Stepwise Verification [R5] (EMNLP 2024) | Verifier flags incorrect steps; prompt remedies | Same restricted AST parser & SymPy symbolic verifier as $G$ | No persistent diagnostic controller, no multi-turn memory ($C_{\text{commit}} = 0\%$). |
| **B3** | **Bayesian Diagnostic Tutor** | Classical BKT [R17] / Calibrated Bayes | Categorical likelihood updates over misconceptions | Small likelihood model using GonitSathi priors and observation categories | Updates naively on every observation; no de-duplication or admission governance. |
| **B4** | **Validated Learner-State Tutor** | IntelliCode [R1] (EACL 2026) | Single-writer centralized validation with assistance-sensitive BKT | Central BKT tracker updating $P(\text{Mastery})$ with single-writer schema validation | Lacks bidirectional claim contestation and multi-turn independent evidence gating. |
| **B5** | **Plan & Assessment Memory** | ScaffoldLM [R2] (ACL 2026) | Stepwise scaffold plan with Assess-Act-Track-Record loop | Tracks step progression index ($k$ of $N$) and remediates current stalled step | Step-completion memory lacks entropy gating and bounded diagnostic probing ($N_{\text{probe}} \le 1$). |
| **B6** | **Diagnostic Reasoning Workspace** | SLOW [R3] (AIED 2026) | Explicit diagnostic workspace with counterfactual validation | Internal counterfactual simulation checking arithmetic slip vs conceptual error | Uses internal self-reflection turns rather than selective human interaction probes. |
| **G** | **GonitSathi Controller** | **Proposed Method** | Governed evidence, revisable diagnostic state, bounded probing | Full pipeline: normalizer $\to$ verifier $\to$ admission governor $\to$ belief model $\to$ probe policy | **Enforces 2-observation rule, evidence provenance, and bounded probing ($R_{\text{commit}} = 0\%$).** |

---

## 2. Resource & Budget Match Guarantees (§9.1)

All systems are evaluated under strictly controlled matching:
1. **Model Budget**: When neural inference is active, prompt templates are capped at 4,096 tokens, outputs at 256 tokens, with greedy deterministic decoding.
2. **Tool Access**: Symbolic verifier access uses the identical SymPy sandbox and AST validator.
3. **Disclosure Policy**: All systems are subject to the same Socratic non-leakage constraint (no final answer disclosure on initial student error).
