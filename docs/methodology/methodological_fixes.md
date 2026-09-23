# Methodological Fixes and Protocol Corrections (§2.2)

This document formalizes the 8 mandatory corrections to the conceptual design proposed in `GonitSathi_Research_Report_v2.pdf`, as mandated by Section 2.2 of the *GonitSathi RA Guideline*.

---

### Fix 1: Error Verification Factor Decoupling
* **Source Report Defect:** The source report defined a verification discount factor $R_{\text{verif}}$ such that when a student's calculation was mathematically wrong ($V = 0$), $R_{\text{verif}}$ collapsed to 0, zeroing out the entire evidence score.
* **Correction:** Distinguish an *untrustworthy observation* (e.g. unparseable gibberish, hallucinated text) from a *reliably verified mathematical error*. When an equation evaluates to `invalid` against the problem constraints, it constitutes high-confidence diagnostic evidence supporting a specific error hypothesis (e.g., wrong formula, incorrect percentage base). Mathematical invalidity must never zero out diagnostic evidence.

### Fix 2: Calibrated Belief Engine vs. Uncalibrated Multiplicative Heuristics
* **Source Report Defect:** Diagnostic reliability was computed as a naive scalar product: $R = C \times I \times S \times D \times \tau$. Multiplied across multiple factors, this caused arbitrary numerical decay with no probabilistic grounding.
* **Correction:** Treat multiplicative factor chains as uncalibrated heuristic baselines. Implement a proper categorical/multinomial belief distribution over candidate diagnostic causes (e.g., $C \in \{\text{misconception}_i, \text{slip}, \text{unknown}\}$), updating priors with log-likelihood ratios conditioned on verified observation features.

### Fix 3: Log-Space Arithmetic and Statistical Calibration
* **Source Report Defect:** Taking the logarithm of factor products ($\log R = \sum \log f_i$) was claimed to "fix probability decay and calibrate the student model."
* **Correction:** Log-space computation prevents floating-point underflow in software; it does *not* alter the underlying statistical distribution or provide empirical calibration. Calibration must be evaluated using Brier scores and reliability diagrams against held-out ground truth. Zero-probability factors must be handled explicitly with Laplace smoothing or floor clipping.

### Fix 4: Expected Information Gain with a Principled Response Model
* **Source Report Defect:** The probe selector maximized entropy reduction ($H_{\text{prior}} - H_{\text{posterior}}$) without specifying how student response probabilities $P(\text{response} \mid \text{cause})$ are estimated.
* **Correction:** Formulate an explicit discrete response model over probe outcomes, including: correct answer, expected diagnostic distractor answer, unrecognized invalid response, and silence/skip. Probes are ranked by expected Shannon information gain penalized by probing cost.

### Fix 5: Dynamic and Revocable Learner State Claims
* **Source Report Defect:** Once a misconception was classified as "confirmed", it was treated as a permanent trait in the student profile.
* **Correction:** All learner claims are time-stamped, context-dependent, and revocable. The controller maintains explicit `provisional`, `active`, `contested`, and `retracted` states. If subsequent independent observations contradict an active misconception, the claim transitions to `contested` and is subsequently `retracted`. Raw observation records are permanently retained.

### Fix 6: Multi-Strategy Equivalence vs. Single Canonical Solution Graph
* **Source Report Defect:** The tutor enforced alignment against a single canonical DAG path, treating any divergence as an error.
* **Correction:** Competitive BCS math problems frequently permit multiple legitimate algebraic and arithmetic solution strategies. The verifier checks semantic equivalence using SymPy simplification ($expr_{\text{student}} - expr_{\text{target}} == 0$) across known valid alternative pathways. Only unprovable or inconsistent relations are classified as errors.

### Fix 7: Verification Guardrails for Generated Natural Language
* **Source Report Defect:** Passing symbolic checks on student equations was assumed to guarantee that the LLM tutor's generated Bengali natural language response was mathematically sound and pedagogical.
* **Correction:** Symbolic checking of student steps does not prevent generative language models from hallucinating explanations, introducing units erroneously, or leaking final answers. A post-generation leakage and fact guardrail audits all realized responses before release.

### Fix 8: Grounded Citation and Empirical Claim Boundary
* **Source Report Defect:** Broad secondary claims asserted universal researcher consensus, total elimination of hallucinations, and claimed tokenization was the sole driver of Bengali performance gaps.
* **Correction:** Retain only empirical findings directly backed by verified tables, formal baselines, and peer-reviewed citations (R1–R18). Bayesian Knowledge Tracing (BKT) and single-writer architectures are acknowledged as strong valid baselines, not dismissed.
