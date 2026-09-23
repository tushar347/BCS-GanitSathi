# Inherited Metric Claim Ledger (§2.1 Audit)

**Last repository reconciliation:** 2026-09-22

**Current decision:** No repository-generated quantitative performance claim is cleared for the
submission. The Update 2/3 values remain development diagnostics until they are reproduced by a
complete, registered, independently validated run.

This ledger audits all quantitative statements, benchmark figures, and performance claims inherited from the predecessor research synthesis (`GonitSathi_Research_Report_v2.pdf`). In accordance with §2.1 and §17.3 of the *GonitSathi Research Plan*, all unverified historical numbers are strictly classified as development motivation until reproduced under the frozen OE-Agent evaluation protocol.

| Inherited Metric | Source Report Claim | Historical Task / Denominator | Git Commit / Dataset Asset | Status & Evidence Grade | Decision for OE-Agent Submission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Calculation Precision** | 100% precision via SymPy symbolic execution engine | Verified algebraic simplification steps on synthetic BCS items ($N=540$) | Inherited Educational Reasoning Engine (v1.2.0-legacy) | **Development Motivation Only** (Tool capability bounded to supported subset) | Restrict claim to "100% precision within supported elementary algebra subset". Measure unassisted student steps separately. |
| **Cache Lookup Latency** | 1.25 ms execution cache response time | Exact-match SHA-256 state cache on local Redis/in-memory store | Local development benchmark (synthetic traces) | **Historical Baseline Only** (Does not reflect full controller pipeline latency) | Do not report as tutoring efficiency. Report end-to-end P50/P95 latency of the full agent controller. |
| **Verifier Accuracy** | 90.0% accuracy on multi-step solution DAGs | Evaluated against synthetic Bengali-to-SymPy parsed transitions ($N=540$) | Legacy synthetic suite `eval_dag_v1.json` | **Legacy Synthetic Only** (Untested on noisy authentic student text) | Re-evaluate verifier accuracy on genuine human BCS student attempts with spelling/unit noise. |
| **Small Model GSM8K Accuracy** | 12% accuracy using unprompted Qwen2.5-1.5B | 50 English GSM8K items tested zero-shot without tools | Legacy quick-probe script ($N=50$) | **Informal Scoping Only** (Small sample, English, zero-shot) | Cite strictly as qualitative justification that small SLMs fail at unassisted end-to-end mathematical generation. |
| **Diagnostic Hallucination Rate** | 68% diagnostic misattribution in naive LLMs | Unconstrained zero-shot prompt on 100 ambiguous errors | Anecdotal survey from prior exploratory runs | **Uncalibrated Baseline** (Lacks formal double-annotation protocol) | Replaced by Baseline $B_1$ in Main Experiment E1 using double-adjudicated test sets. |

---

## Current Repository-Generated Claims

| Claim or artifact | What the repository supports | Blocking issue | Submission decision |
| :--- | :--- | :--- | :--- |
| **411 unique family identifiers** | Recursive ingestion yields 411 distinct IDs and draft 207/102/102 ID manifests. | Content-level disjointness fails for at least one exact question-and-options duplicate across train/dev, and the manifests contain no explicit content hashes. | **Structure confirmed; benchmark freeze not verified.** |
| **1,536 histories/steps** | The current main ingester generates one-event histories: one correct response plus one history per possible mistake. | These are generated evaluation cases, not independently observed or adjudicated human student trajectories. | **Describe only as generated cases.** |
| **28-family pilot** | A separate artifact contains four constructed trajectory types per family. | Independent double-annotation and adjudication outputs were not found in the repository. | **Development pilot only.** |
| **Full dev/test E1 run** | Committed summaries declare 102 families per split. | The current family-resolution path silently skips unresolved DAGs: the stored dev/test outputs contain only 52/70 histories despite declaring all 102 families. | **Invalid as a complete E1 result; rerun required.** |
| **First-error accuracy** | The evaluator emits a numeric value. | Predicted verifier reasons/causes are compared with `history_type`, which is a different label namespace. | **Metric quarantined pending semantic repair and tests.** |
| **0% unsupported-commitment risk** | GonitSathi's stored output has 0% commitment coverage. | No commitments means the mathematical risk is undefined; the harness currently converts that case to `0.0`. | **Must not be described as evidence of safe diagnosis.** |
| **B0–B6 versus GonitSathi comparison** | A common code interface and preliminary offline output artifacts exist. | B1 defaults to an offline simulator, B6 counts a simulated internal reasoning call as a neural call, source-faithfulness/matched-resource execution is not demonstrated, and runs are unregistered. | **Engineering smoke comparison only.** |
| **Latency, token, and model-call figures** | A small CPU-path profile and proxy counters exist. | The profile covers five families; token counts are proxies and some recorded neural calls do not correspond to live model execution. | **Do not present as model-serving cost.** |
| **112 passing tests / 8-of-8 gate** | On 2026-09-22, `.venv/bin/python scripts/verify.py` passed all eight checks and 112 tests under Python 3.11.16. | This local engineering gate covers its implemented checks only; it does not validate benchmark labels, metric semantics, or experimental claims, and the full CI version matrix was not reproduced in this audit. | **May be reported as dated local engineering verification, not scientific validation.** |

To release any row above, fix the stated blocker, freeze inputs and scoring, register the run in
`evaluations/registry/run_manifest.csv`, retain the detailed output/failure artifact, and obtain
the named independent validation.

---

## Audit Invariant
No metric in this ledger may be cited in the ACML 2026 workshop manuscript as a measured property of GonitSathi-BCS without an active entry in `evaluations/registry/run_manifest.csv` referencing an auditable commit hash and seed.
