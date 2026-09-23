# GonitSathi Supervisor Checkpoint — Update 1

| Package field | Status |
| --- | --- |
| Version | v1.0, 13 September 2026 |
| RA1 assembly | Complete |
| Required validator | Supervisor — decision pending |
**Stage:** Protocol checkpoint before benchmark freeze or large experimental runs  
**Evidence boundary:** No new performance, learning, or efficiency result is claimed in this document.

## Decision Requested

Approve, conditionally approve, or request revision of the contribution, RQ1–RQ5, primary metric and operating rule, baseline set, benchmark scope, and immediate priorities. Approval authorizes continued protocol development; it does not certify implementation quality or experimental results.

## Contribution and Research Questions

**Paper in one sentence.** We investigate whether provenance-aware diagnostic state updates and bounded information-seeking interactions make small open-weight tutoring agents more reliable and efficient on ambiguous Bengali mathematics attempts.

**Primary directional hypothesis.** Against the strongest matched state-memory baseline, GonitSathi will lower unsupported-commit risk while retaining useful diagnostic coverage. A system that merely abstains more often does not satisfy this hypothesis.

| ID | Testable question | Primary evidence |
| --- | --- | --- |
| RQ1 | Does evidence governance reduce unsupported diagnostic commitments at comparable coverage? | Risk–coverage curve, frozen operating point, calibration |
| RQ2 | Does a selected probe outperform an equally costly generic or random probe? | Diagnostic change after an observed response; inappropriate-intervention rate |
| RQ3 | Does the approach offer a useful quality–cost trade-off across small model sizes? | Accepted intervention quality versus latency, tokens, calls, and memory |
| RQ4 | Does it resist assistance contamination, contradictory evidence, and language perturbations? | Paired stress tests and recovery after correction |
| RQ5 | Does it help actual learners? | Blinded expert judgment; a learner study is a separate later experiment |

## Proposed Method

The controller enforces a single deterministic state-write path:

`student event → reversible Bengali normalization → restricted symbolic verification → evidence admission → categorical diagnostic belief → optional one-probe decision → instructional action → Bengali realization → release guardrail`

Observed events, verification results, diagnostic hypotheses, learner claims, and instructional actions are conceptually distinct. Models may propose interpretations or wording, but they cannot directly mutate persistent learner state. Unresolved interpretations are logged without belief updates; verified wrong work remains evidence of an error; assisted work is distinguished from independent work; correlated events are not counted twice; and claims must remain contextual and revocable.

## Eight Methodological Corrections

1. Do not zero evidence because the student’s mathematics is wrong; a reliably verified error is diagnostic evidence.
2. Replace uncalibrated factor products with a categorical belief distribution over competing causes.
3. Treat log-space arithmetic as numerical stabilization, not statistical calibration.
4. Select probes using an explicit response model and expected information gain.
5. Make learner claims time-stamped, contextual, contestable, and retractable.
6. Accept equivalent and alternative valid solution strategies.
7. Audit generated explanations separately for factual and disclosure failures.
8. Keep inherited claims separate from results reproduced under the frozen protocol.


## Primary Evaluation Protocol

**Strongest competing explanation.** A simpler Bayesian diagnostic tutor (B3), given the same verifier, observation categories, templates, and probe bank, may match GonitSathi. Any apparent risk reduction may otherwise come from greater abstention, privileged reference access, the extra student response, additional compute, or the shared release guard rather than evidence governance.

**Primary metric.** Unsupported-commit risk is:

`active diagnostic commitments not justified by adjudicated evidence / all active diagnostic commitments`

Risk is undefined when no commitment is made. It must be reported with counts, a 95% confidence interval, commitment coverage, and useful-action coverage. The main comparison is the full risk–coverage curve plus a frozen common-coverage comparison.

**Operating-point rule.** Select the threshold using development data by maximizing coverage while keeping the upper 95% confidence bound on unsupported-commit risk below 5%. If no setting satisfies the rule, report that outcome and the complete curve. Freeze a common coverage point, provisionally 60% if attainable by both systems, before examining test results.

**Independent sample unit.** The problem family—not a paraphrase, history, turn, seed, or model run—is the independent unit. Statistical intervals and paired comparisons must cluster by family.

**Primary systems.** B0 reviewed rule/template tutor; B1 strong prompted tutor; B2 verify-then-generate; B3 Bayesian diagnostic tutor; B4 validated learner-state adaptation; B5 plan/assessment-memory adaptation; B6 diagnostic-workspace adaptation; G GonitSathi. All receive the same student-visible history, verified problem resource, permitted actions, output policy, and applicable budgets.

<div style="page-break-after: always;"></div>

**Benchmark target.** Core target: 300 families across six BCS topic groups, split 150/75/75 into train/development/test, with four fixed histories per family. The independent 20-family pilot must establish annotation feasibility before committing to this scale. Interactive target: 120 scenarios from at least 60 test families.

| Split evidence | Current value |
| --- | --- |
| Train hash | NR — dataset not yet populated |
| Development hash | NR — dataset not yet populated |
| Test hash | NR — dataset not yet populated |
| Family-disjointness audit | Pending RA2 dataset and RA1 validation |

**Compute planning estimate—not a measured result.** Use Qwen3-4B as the initial backbone and 1.7B/8B for scale checks, subject to license and revision verification. The fixed test plan is 8 systems × 300 histories = 2,400 evaluations. The interactive plan is 8 systems × 120 scenarios × 3 seeds = 2,880 episodes; at six turns and two neural calls per turn, the upper bound is 34,560 tutor calls, excluding simulator calls. Initial caps are 4,096 input tokens per call, 256 output tokens for structured evidence, 256 for tutor response, one probe per episode, and four symbolic checks per turn. Hardware fit, mean tokens, latency, and monetary/energy cost remain unmeasured.

## Current Progress and Evidence

- The claim ledger, eight methodological corrections, R1–R18 literature matrix, expert rubric, core schemas, normalizer, verifier, controller, metrics, and test definitions exist. RA1 completed the Task 1.3 and Task 1.7 audits with Conditional Passes; owner responses and gate-closing actions remain pending.
- The core implementation is a prototype; older controller modules and active schemas are inconsistent, and runtime thresholds do not fully match configuration files.
- Benchmark directories and split manifests are empty; the 20-family pilot, hashes, and annotation-agreement results do not yet exist.
- Baselines B0–B6 are not implemented, the tuning loop is a scaffold, and the experiment registry has no completed run.
- The canonical verification gate was added and baseline-tested: syntax, configuration/schema generation, and Git whitespace passed; the full gate correctly failed on the local Python 3.13 runtime, missing development dependencies, and three legacy controller import errors. A supplementary isolated run previously passed 17 tests under Python 3.13; a green Python 3.11 gate remains required.

## Principal Risks and Immediate Work

| Risk | Immediate control |
| --- | --- |
| Governance claims exceed implementation | Task 1.3 and Task 1.7 audits issued Conditional Passes; RA2/RA3 resolve the recorded method, production-schema, immutability, validation, and API-drift gaps |
| Benchmark infeasible or labels unreliable | RA2 completes the 20-family pilot; RA1 checks ambiguity, agreement, adjudication, and authoring cost |
| Gains caused by abstention or extra resources | Freeze risk–coverage rule; include equal-call, equal-token, and equal-interaction controls |
| Probe response model is misspecified | Review response categories, collect actual responses, and compare selected, random, fixed, and generic probes |
| Timeline cannot support full scope | Preserve B3 and the governance/probing factorial test; reduce topics or use the four-page scope before weakening controls |

**Next deliverables:** (1) RA2/RA3 responses and corrective changes for the Task 1.3 and Task 1.7 findings; (2) RA2’s 20-family pilot with agreement and cost estimates; (3) corrected canonical controller and reproducible Python 3.11 environment; (4) B0–B3 runnable interfaces; (5) dev trace and pilot compute profile; (6) frozen protocol review.

## Evidence Dependencies Before Final Sign-Off

- [ ] Ten representative annotated examples — RA2 supplies them through Task 1.8; RA1 audits them.
- [ ] Two reviewed end-to-end traces — RA3/RA4 supply them; the Supervisor reviews them.

These dependencies do not block RA1’s package assembly, but they do block final checkpoint validation.

## Supervisor Decision Record

**Decision:**

- [ ] Approve the proposed protocol direction.
- [ ] Conditionally approve subject to the listed actions.
- [ ] Revise and resubmit the checkpoint.

- **Required revisions or conditions:** ________________________________________________
- **Supervisor:** ____________________
- **Date:** ____________________

