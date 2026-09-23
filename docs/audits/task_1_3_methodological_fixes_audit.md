# Task 1.3 Audit — Eight Methodological Corrections

**Audit ID:** GS-U1-T1.3-AUDIT-001  
**Audit date:** 2026-09-13  
**Owner of audited artifact:** RA3  
**Independent auditor:** RA1  
**Audited artifact:** `docs/methodological_fixes.md`  
**Overall verdict:** **Conditional Pass**

## Decision

The eight corrections in `docs/methodological_fixes.md` are directionally consistent with Section 2.2 of the GonitSathi RA Guideline. Fix 1 is implemented and directly exercised by the current integration suite. Fixes 2–8 are valid methodological intentions, but each has at least one wording, implementation, validation, or evidence gap that must be resolved before protocol freeze.

Task 1.3’s audit activity is complete. This verdict does **not** certify the full method as experiment-ready, empirically calibrated, persistent, or safe. The required actions below remain assigned to their implementation and evaluation owners.

## Scope and Evidence

Reviewed:

- `docs/GS_Main_Guide.pdf`, Section 2.2 and related method/evaluation requirements.
- `docs/methodological_fixes.md`.
- `docs/claim_ledger.md` and `docs/literature_matrix.md`.
- Active controller, verifier, normalizer, prompt-contract, benchmark, and evaluation modules under `src/`.
- Existing unit and integration tests under `tests/`.
- `scripts/tune_thresholds.py` and the experiment registry.

Not reviewed as completed evidence:

- No benchmark splits, adjudicated labels, calibration outputs, response-model estimates, experiment runs, or persistent-state store currently exist.
- No generated-language model is integrated into the active controller, so generative factual safety cannot yet be measured end to end.

## Test Evidence

| Check | Result | Interpretation |
| --- | --- | --- |
| Existing repository suite, cache and bytecode generation disabled | **17 passed in 1.72 s** | Supports the currently tested prototype paths |
| Runtime used | Python 3.13.3 with temporary Pydantic, SymPy, and pytest dependencies | Supplementary only |
| Required project runtime | Python 3.11 | Not available locally; required-runtime validation remains pending |
| Repository artifacts from test run | None expected (`PYTHONDONTWRITEBYTECODE=1`, pytest cache disabled) | Working tree must remain the source of truth |

Passing tests establish conformance only for their assertions. They do not demonstrate empirical calibration, benchmark validity, long-term learner-state persistence, probe usefulness, or complete output safety.

## Finding Summary

| Fix | Correction | Documentation | Implementation | Verdict |
| --- | --- | --- | --- | --- |
| 1 | Preserve verified wrong work as evidence | Aligned | Implemented and tested | **Pass** |
| 2 | Use categorical beliefs instead of heuristic products | Aligned with qualification | Implemented with hand-authored likelihoods; not calibrated | **Conditional Pass** |
| 3 | Separate log-space stability from calibration | Aligned | Brier metric exists; calibration protocol/results absent | **Conditional Pass** |
| 4 | Use EIG with an explicit response model | Aligned in principle | Selection exists; estimation and response ingestion incomplete | **Conditional Pass** |
| 5 | Make learner claims contextual and revocable | Aligned in principle | State labels/transitions exist; durable claim model does not | **Conditional Pass** |
| 6 | Accept multiple valid strategies | Mostly aligned; one wording defect | Alternative/equivalence checks exist; constraints and coverage incomplete | **Conditional Pass** |
| 7 | Audit generated responses independently | Aligned in principle | Leakage matching exists; factual/unit audit does not | **Conditional Pass** |
| 8 | Enforce grounded empirical claims | Mostly aligned; source-status wording too broad | Claim ledger exists; experimental linkage remains unexercised | **Conditional Pass** |

## Detailed Findings

### Fix 1 — Error Verification Factor Decoupling

**Verdict: Pass**

Evidence:

- `src/controller/evidence_admission.py:47-48` explicitly admits `INVALID` mathematics as `valid_evidence_of_mathematical_error`.
- `tests/integration/test_minimal_cases.py:90-108` verifies that a wrong step is admitted, increases the relevant error belief, and does not collapse the distribution.
- Unresolved and unverifiable observations are kept out of belief updates.

Qualification:

- “High-confidence evidence supporting a specific error hypothesis” should not imply that every wrong equation uniquely identifies its cognitive cause. Ambiguous wrong work must retain multiple candidates or remain unresolved.

Required action:

- Preserve the current admission behavior and add ambiguous-error cases during benchmark validation. **Owner: RA2/RA3.**

### Fix 2 — Categorical Belief Engine

**Verdict: Conditional Pass**

Evidence:

- `src/controller/belief_updater.py:24-31` defines priors over competing causes.
- `src/controller/belief_updater.py:134-151` performs likelihood multiplication and posterior normalization.
- Assistance-conditioned likelihood tables and candidate-cause boosts are present.

Gaps:

- The likelihoods are hand-authored and have not been fitted or calibrated on held-out data.
- The implementation uses direct probability multiplication, not the correction document’s stated log-likelihood-ratio update.
- Calling the class `CalibratedBeliefUpdater` overstates the current evidence.
- The candidate-cause inventory is narrow and dominated by one percentage misconception plus generic slips.

Required action:

- Until dev-set calibration is completed, describe the module as a categorical Bayesian belief updater with provisional likelihoods. Document how priors and likelihoods are estimated and frozen. **Owner: RA3; validator: RA4.**

### Fix 3 — Log-Space Arithmetic and Statistical Calibration

**Verdict: Conditional Pass**

Evidence:

- The correction correctly states that log-space arithmetic prevents underflow but does not create calibration.
- `src/evaluation/metrics.py:51-78` implements multiclass Brier score.
- Current likelihood tables avoid zero values for the modeled valid/invalid observations.

Gaps:

- No negative log likelihood, expected calibration error, reliability-diagram generator, or held-out calibration result exists.
- `scripts/tune_thresholds.py` is a scaffold and currently substitutes zero risk and coverage rather than running histories.
- Direct multiplication remains vulnerable to underflow over sufficiently long evidence sequences.

Required action:

- Add the predeclared calibration metrics and reliability plot; implement real dev-set threshold/calibration execution; introduce stable arithmetic when longitudinal sequences are enabled. **Owner: RA3/RA4; cross-check: RA1.**

### Fix 4 — Expected Information Gain and Response Model

**Verdict: Conditional Pass**

Evidence:

- `DiagnosticProbe.response_model` represents conditional response probabilities.
- `src/controller/probe_selector.py:37-89` computes expected information gain from posterior entropy.
- `src/controller/probe_selector.py:92-123` applies the uncertainty gate, burden penalty, and one-probe cap.
- The integration suite verifies that the probe budget is not exceeded.

Gaps:

- No provenance or estimation procedure exists for the response probabilities.
- Required outcomes such as invalid/unrecognized responses and silence/timeout are not enforced by the schema.
- Conditional probabilities are not validated for range or normalization.
- The controller selects a probe but has no dedicated path that classifies the observed probe response and updates the belief using that response model.
- Probe usefulness has not been compared with random, fixed, or generic equal-interaction controls.

Required action:

- Specify response categories and missing outcomes, validate probability tables, implement actual response ingestion, estimate/freeze models on development evidence, and run the required controls. **Owner: RA3; data owner: RA2; validator: RA4.**

### Fix 5 — Dynamic and Revocable Learner-State Claims

**Verdict: Conditional Pass**

Evidence:

- `ClaimStatus` defines provisional, active, contested, and retracted states.
- `src/controller/belief_updater.py:164-210` uses independent evidence groups and implements activation, contesting, and retraction rules.
- The integration suite checks assisted success, contradiction records, and bounded claim behavior.
- The controller retains an in-memory observation log across an episode reset.

Gaps:

- There is no separate `LearnerClaim` schema; hypothesis probability and claim status are combined in `HypothesisRecord`.
- The active belief/hypothesis state is cleared by `reset_episode`, so longitudinal and cross-context revision is not implemented.
- “Permanently retained” is not satisfied by an in-memory list with no durable storage contract.
- Observation models are mutable; admission changes the captured record after construction.
- `latest_update` is initialized but not updated during later transitions.

Required action:

- Define the distinct immutable observation and contextual learner-claim contracts, update timestamps on transitions, and specify persistence and cross-context scope before longitudinal claims are evaluated. **Owner: RA3; schema validator: RA1/RA2.**

### Fix 6 — Multi-Strategy Equivalence

**Verdict: Conditional Pass**

Evidence:

- `ReferenceStep.alternative_forms` records reviewed alternatives.
- `src/verifier/symbolic_verifier.py:233-258` checks primary and alternative expressions.
- `src/verifier/symbolic_verifier.py:299-334` checks symbolic and proportional equation equivalence.
- Tests cover a listed alternative strategy.
- Unrecognized or undeclared-variable strategies can return `UNSUPPORTED` rather than `INVALID`.

Gaps:

- The correction’s final sentence says “unprovable or inconsistent relations” are errors. This conflicts with the required distinction: unprovable relations should normally be `UNVERIFIABLE` or `UNSUPPORTED`; only demonstrated inconsistency should be `INVALID`.
- `ProblemReferenceDAG.boundary_constraints` is declared but not applied during verification.
- Test coverage does not include multiple solution sets, constraints, inequalities, domain assumptions, or unlisted but valid multi-step strategies.

Required action:

- Correct the wording, implement relevant assumptions/constraints, and extend tests with reviewed alternative and unsupported cases. **Owner: RA3; validator: RA2.**

### Fix 7 — Natural-Language Release Guardrail

**Verdict: Conditional Pass**

Evidence:

- `src/controller/guardrail.py:43-98` checks supplied final-answer strings and decisive-calculation strings and substitutes reviewed Bengali fallbacks.
- The controller passes every selected action through this release audit.
- Prompt contracts limit realizer facts and question count.

Gaps:

- The active guardrail does not validate mathematical facts, units, assumptions, paraphrased answers, equivalent calculations, or cumulative disclosure.
- Matching depends on caller-supplied prohibited strings and simple substring/regex detection.
- No generated realizer is integrated, so the stated post-generation safety path has not been tested end to end.
- There are no direct guardrail tests for authorized worked solutions, false blocking, unit errors, or multi-turn leakage.

Required action:

- Narrow the current claim to a lexical leakage guard, then implement and test mathematical/factual, unit, disclosure-equivalence, and cumulative-dialogue audits before describing it as a fact guardrail. **Owner: RA3; validator: RA4/RA1.**

### Fix 8 — Grounded Citation and Empirical Claim Boundary

**Verdict: Conditional Pass**

Evidence:

- `docs/claim_ledger.md` labels inherited numbers as development motivation, historical, legacy synthetic, informal, or uncalibrated evidence.
- Its audit invariant forbids treating an inherited number as a GonitSathi result without an experiment-registry entry.
- `docs/literature_matrix.md` now covers R1–R18 and identifies preprints and a position paper explicitly.
- `evaluations/registry/run_manifest.csv` defines traceability fields, but currently contains no completed runs.

Gaps:

- The correction says claims must be backed by “peer-reviewed citations (R1–R18),” but the matrix explicitly contains preprints and a position paper. Peer review cannot be asserted for the entire set.
- Matrix entries are summaries, not a complete reference list with versions, URLs/DOIs, code licenses, and method-section verification records.
- No manuscript-to-ledger or result-to-registry audit has yet been exercised because results and manuscript claims do not exist.

Required action:

- Replace “peer-reviewed citations” with “verified primary sources whose venue and review status are stated accurately.” Complete source/version records and repeat the audit before manuscript freeze. **Owner: RA1; validator: RA4/RA3.**

## Required Actions Before Protocol Freeze

The following are gate-blocking for claims about the corresponding mechanism:

1. Qualify “calibrated” until likelihoods and predictions are evaluated on held-out data.
2. Implement and validate the real threshold/calibration pipeline.
3. Define how probe-response probabilities are estimated and ingest actual probe responses.
4. Separate immutable observations, diagnostic hypotheses, and durable contextual learner claims.
5. Correct Fix 6’s treatment of unprovable relations and test boundary constraints/alternatives.
6. Describe the current output guard as lexical leakage detection until factual and cumulative audits exist.
7. Correct Fix 8’s blanket peer-review wording and complete primary-source records.
8. Re-run the suite under the required Python 3.11 environment and record the result.

## Sign-Off

**RA1 audit conclusion:** Conditional Pass. The correction document is accepted as the methodological direction for continued development, subject to the listed wording and implementation actions. It must not be cited as evidence that all eight mechanisms are fully implemented or empirically validated.

**RA3 response:** Pending.  
**Supervisor acknowledgement:** Pending.  
**Protocol-freeze closure:** Pending resolution or explicit deferral of all gate-blocking actions.

