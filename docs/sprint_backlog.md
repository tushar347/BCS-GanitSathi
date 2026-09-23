# Sprint Backlog: Phased Roadmap to OE-Agent @ ACML 2026

**Status reconciled with repository:** 2026-09-22

**Canonical status:** `docs/milestones.md`

Checkboxes in this historical sprint plan mean that the named deliverable artifact is present;
they do not by themselves confer the **Verified** status defined in `docs/milestones.md`. Tasks
whose wording includes unfinished validation remain open, with existing implementation noted
explicitly. Preliminary Update 2/3 metrics are not submission-ready results; see
`docs/claim_ledger.md`.

## Update 1 (13 Sept) – Specification, Claim Audit & Pilot Initialization
- [x] Task 1.1: Verify workshop submission parameters, page limits, and anonymous template on OpenReview. (Owner: RA1 | Validator: RA4)
- [x] Task 1.2: Construct `docs/claim_ledger.md` for historical numbers (12% GSM8K, 100% SymPy precision, 1.25 ms cache). (Owner: RA1 | Validator: RA4)
- [x] Task 1.3: Document 8 methodological corrections in `docs/methodological_fixes.md` (fixing zero-on-error product formula). (Owner: RA3 | Validator: RA1)
- [x] Task 1.4: Implement schema for core objects: Observation, Verification, Hypothesis, Claim, Action. (Owner: RA3 | Validator: RA2)
- [x] Task 1.5: Finalize literature comparison matrix across primary sources R1–R18. (Owner: RA1 + RA4 | Validator: RA3)
- [x] Task 1.6: Finalize one-sentence paper contribution and primary hypotheses RQ1–RQ5. (Owner: RA1 | Validator: Supervisor)
- [x] Task 1.7: Write Pydantic event schema matching Appendix A.1 in `src/controller/schemas.py`. (Owner: RA2 + RA3 | Validator: RA1)
- [ ] Task 1.8: Independently double-annotate and adjudicate an agreed subset of the existing 28-family pilot, then calibrate the expert scoring rubric. (Owner: RA2 | Validator: RA1) — The original task target was 20 families; the agreed final pilot size still needs to be recorded.
- [x] Task 1.9: Assemble 2-page supervisor checkpoint package. (Owner: RA1 | Validator: Supervisor) — RA1 assembly complete; Supervisor validation pending.

## Update 2 (19 Sept) – Normalizer, Verifier & Baselines B0–B3
- [x] Task 2.1: Implement bilingual normalizer (Bengali/ASCII numeral conversion, reversible mapping). (Owner: RA3 | Validator: RA2)
- [x] Task 2.2: Implement restricted math parser and SymPy symbolic verifier. (Owner: RA3 | Validator: RA2)
- [x] Task 2.3: Implement evidence admission with assistance tagging and event de-duplication. (Owner: RA3 | Validator: RA4)
- [x] Task 2.4: Implement categorical belief model over candidate causes. (Owner: RA3 | Validator: RA4)
- [x] Task 2.5: Code minimal verification integration tests (Appendix A.3). (Owner: RA3 | Validator: RA2)
- [x] Task 2.6: Draft prompt contracts for evidence extractor (Appx B.1) and response realizer (Appx B.2). (Owner: RA3 | Validator: RA2)
- [x] Task 2.7: Author first batch of problem families across 6 BCS topics. (Owner: RA2 | Validator: RA1)
- [x] Task 2.8: Build Baselines: B0 (Rule/Template), B1 (Prompted), B2 (Verify-then-generate), B3 (Bayesian Diagnostic). (Owner: RA4 | Validator: RA3)
- [ ] Task 2.9: Produce and independently review one end-to-end logged development trace. (Owner: RA3 + RA4 | Validator: Supervisor) — Runner implemented; committed trace evidence and review are pending.

## Update 3 (23 Sept) – Benchmark Freezing, Baselines B4–B6 & Profiling
- [ ] Task 3.1: Double-annotate test histories with adjudication. (Owner: RA2 | Validator: RA1) — Histories exist, but no independent annotation or adjudication artifacts were found.
- [ ] Task 3.2: Run content-aware contamination checks and freeze benchmark splits with explicit content hashes. (Owner: RA2 | Validator: RA1) — Draft 207/102/102 family-ID manifests exist; at least one exact question-and-options duplicate crosses train/dev, and the manifests record no content hashes.
- [ ] Task 3.3: Build and validate protocol-faithful Baselines B4 (IntelliCode adaptation), B5 (ScaffoldLM adaptation), and B6 (SLOW adaptation). (Owner: RA4 | Validator: RA3) — Code-level adaptations exist; source-faithfulness and applicable live-model/matched-resource validation are pending.
- [x] Task 3.4: Complete baseline adaptation differences table in `docs/methodology/baseline_differences.md`. (Owner: RA4 | Validator: RA1)
- [ ] Task 3.5: Run pilot token and call profiling; log hardware specs. (Owner: RA4 + RA3 | Validator: RA1) — A five-family CPU-path profile exists; model-token, actual-call, and protocol-scale profiling remain pending.

## Update 4 (26 Sept) – Protocol Freeze, Primary Runs (E1) & Probing Ablations (A1–A9)
- [ ] Task 4.1: Freeze activation ($\theta_{\text{commit}}$) and entropy ($H_{\text{thresh}}$) thresholds on dev set. (Owner: RA3 | Validator: RA4)
- [ ] Task 4.2: Execute Main Experiment E1: B0–B6 vs. G at matched resources. (Owner: RA4 | Validator: RA3) — Preliminary offline outputs exist, but the evaluator silently skips unresolved families, source-faithful matched execution is not demonstrated, and the run registry is empty.
- [ ] Task 4.3: Populate and validate Main Table: commit risk, coverage, Brier score, first-error accuracy, latency. (Owner: RA4 | Validator: RA1) — A preliminary table exists; first-error and no-commitment risk semantics require correction before rerun.
- [ ] Task 4.4: Execute Ablations A1–A9 (admission, provenance, overwrite, probes). (Owner: RA3 + RA4 | Validator: RA1)
- [ ] Task 4.5: Run $2 \times 2$ factorial test crossing governance and probing. (Owner: RA4 | Validator: RA3)

## Update 5 (30 Sept) – Human Evaluation, Scaling (E3) & Stress Tests (E4–E5)
- [ ] Task 5.1: Execute expert audit on 100 contexts across 3 systems (2 raters + adjudicator). (Owner: RA1 + RA2 | Validator: Supervisor)
- [ ] Task 5.2: Execute model scale experiment E3 (1.7B, 4B, 8B) and plot quality vs. cost. (Owner: RA4 | Validator: RA3)
- [ ] Task 5.3: Run assistance contamination tests and 20-observation stress sequences (E4). (Owner: RA4 | Validator: RA3)
- [ ] Task 5.4: Execute language perturbation stress tests E5. (Owner: RA2 + RA4 | Validator: RA1)
- [ ] Task 5.5: Compute bootstrap confidence intervals and Holm-corrected statistics. (Owner: RA4 | Validator: RA1)

## Update 6 (3 Oct) – Full Manuscript, Reproducibility & Internal Gates
- [ ] Task 6.1: Draft 8-page manuscript according to exact page allocations. (Owner: RA1 | Validator: Supervisor)
- [ ] Task 6.2: Generate Figures 1–3 and Tables 1–3. (Owner: RA1 + RA3 + RA4 | Validator: RA2)
- [ ] Task 6.3: Package reproducibility release (configs, data schemas, scripts, logs). (Owner: RA3 + RA4 | Validator: RA1)
- [ ] Task 6.4: Independent non-author table reproduction. (Owner: Independent RA | Validator: Supervisor)
- [ ] Task 6.5: Complete scientific and manuscript submission gate checklists. (Owner: RA1 + Supervisor)
