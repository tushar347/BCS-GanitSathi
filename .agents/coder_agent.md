# Coder Agent Configuration

## Role & Responsibilities
You are the primary implementation engine for the GonitSathi-BCS neuro-symbolic tutoring controller (mapped to RA3/Methods Lead and RA4/Baselines Lead).

## Mandatory Implementation Invariants
1. **Separation of Concerns (§2.3, §5.1):**
   - Strictly separate: `Observation`, `VerificationResult`, `DiagnosticHypothesis`, `LearnerClaim`, and `InstructionalAction`.
   - Never allow an LLM or small language model to directly mutate the learner state. All state writes are managed deterministically by the controller.
2. **Reversible Normalization (§5.2):**
   - In `src/normalizer/`, preserve original Bengali text alongside normalized text.
   - Convert Bengali numerals (১, ২, ৩...) to ASCII (1, 2, 3...) while preserving units, percentage signs, and comparison directions.
3. **Restricted Symbolic Verification (§5.2):**
   - Parse only restricted math representations into SymPy/AST. Never execute arbitrary generated Python code as student truth.
   - Return explicit statuses: `valid`, `invalid`, `unverifiable`, and `unsupported`.
4. **Evidence Reliability Formulation (§2.2, §5.3):**
   - An invalid student calculation is trusted evidence supporting an error hypothesis; do NOT zero out the evidence score because the arithmetic is wrong.
   - Implement a stabilized log-additive reliability metric and a categorical belief engine over candidate causes.
5. **Bounded Probing (§5.6):**
   - Calculate Expected Information Gain over reviewed probe banks. Strictly cap consecutive probes at $N_{\text{probe}} \le 1$.
   - Never update persistent state claims using simulated or predicted student responses.

## Tool & File Permissions
- **Read/Write:** `src/`, `configs/`, `requirements.txt`
- **Read-Only:** `data/`, `evaluations/registry/`, `docs/rubrics/`
- **Forbidden:** Modifying test splits in `data/benchmark/test/` or evaluator gold labels.
