# GonitSathi-BCS: Evidence-Governed Neuro-Symbolic Tutoring

---

## 1. Project Overview

GonitSathi investigates whether **provenance-aware diagnostic state updates** and **bounded information-seeking interactions** make small open-weight tutoring agents (SLMs, e.g., 7B/8B) more reliable and computationally efficient when diagnosing ambiguous student mathematics attempts in Bengali (specifically targeted at Bangladesh Civil Service preliminary mathematics).

### Core Architectural Invariants (§2.3, §5.1)
1. **Separation of Architectural Concerns:** Strict operational separation between:
   * `ObservationRecord`: Immutable captured student event with verification provenance.
   * `VerificationResult`: Deterministic output from restricted AST / SymPy solver (`valid`, `invalid`, `unverifiable`, `unsupported`).
   * `DiagnosticHypothesis`: Calibrated probabilistic belief over competing causes (misconceptions vs. transient slips).
   * `LearnerClaim`: Context-dependent, timestamped, and revocable epistemic state (`provisional`, `active`, `contested`, `retracted`).
   * `InstructionalAction`: Pedagogical decision strictly constrained by disclosure policies.
2. **Deterministic State Mutation:** Natural language models are strictly forbidden from directly writing to the persistent learner state. All mutations pass through the evidence admission controller.
3. **Calibrated Belief Distribution:** Multi-factor heuristic products are replaced with a calibrated categorical belief engine.
4. **Bounded Diagnostic Probing:** When posterior entropy over candidate causes is elevated, the controller deploys at most **one** targeted probe ($N_{\text{probe}} \le 1$) based on expected information gain before proceeding.
5. **Reversible Bilingual Normalizer:** Maps Bengali numerals (০–৯) to ASCII while preserving original strings, units, and index mappings.
6. **Error Evidence Integrity Guard (§2.2):** A student's mathematically invalid calculation is high-confidence evidence supporting an error hypothesis. Mathematical invalidity must never zero out evidence admissibility.

---

## 2. Environment Setup in Git Bash (Python 3.11 with `uv`)

This repository is strictly standardized on **Python 3.11**. To prevent conflicts with bleeding-edge system distributions (e.g., Arch Linux), virtual environments must be managed via [`uv`](https://github.com/astral-sh/uv).

### Prerequisites
Install `uv` if not already available:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Virtual Environment Initialization
```bash
# 1. Clone repository
git clone git@github.com:rifahnanjiba02-arch/GonitSathi.git
cd GonitSathi

# 2. Pin and install Python 3.11 virtual environment via uv
uv venv --python 3.11

# 3. Activate the virtual environment in Git Bash on Windows
source .venv/Scripts/activate

# 4. Verify Python runtime version
python --version   # Must output Python 3.11.x

# 5. Install pinned project dependencies
uv pip install -r requirements.txt
```

### Repository Verification Gate
In Git Bash, install the development dependencies and run the canonical gate from the
repository root:

```bash
uv pip install -r requirements-dev.txt
python scripts/verify.py
```

The command verifies the Python version and dependencies, compiles Python sources in memory,
parses JSON/YAML configuration, generates Pydantic schemas, imports every `src` module, runs
Ruff correctness checks, checks Git whitespace, and executes the unit/integration suite. It exits
non-zero if any phase fails. A passing gate certifies only these implemented checks; it is not proof
of behavior for which no test, dataset, model, or experimental evidence exists.

To run only the test suite:
```bash
python -m pytest -v tests/
```

---

## 3. Multi-Agent Roster & Team Workflow

To prevent self-evaluating experimental bias, four specialized agent roles are configured under `.agents/` matching Section 15.1 of the research guideline:

| Agent Role | Configuration File | Primary Responsibilities | Mandatory Cross-Verification Duty |
| :--- | :--- | :--- | :--- |
| **RA1: Lead & Governance** | [`.agents/docs_writer_agent.md`](.agents/docs_writer_agent.md) | Venue rule compliance, claim ledger maintenance ([`docs/claim_ledger.md`](docs/claim_ledger.md)), literature matrix ([`docs/methodology/literature_matrix.md`](docs/methodology/literature_matrix.md)), and anonymous manuscript drafting. | Audits data split disjointness, prompt leakage, and baseline fidelity. |
| **RA2: Data & Benchmark** | [`.agents/validator_agent.md`](.agents/validator_agent.md) | Authoring `GonitSathi-Bench` (6 BCS topics), managing 4-history schema per problem family, double-annotation adjudication logistics, and expert rubrics. | Audits prompt contracts to ensure no direct learner-state mutations occur. |
| **RA3: Methods & Engineering** | [`.agents/coder_agent.md`](.agents/coder_agent.md) | Bilingual Normalizer, restricted SymPy verifier, evidence admission engine, belief engine, and output leakage guardrails. | Audits evaluation metrics, latency calculations, and cost profiling. |
| **RA4: Baselines & Profiling** | [`.agents/bug_tracer_agent.md`](.agents/bug_tracer_agent.md) | Implementation of Baselines $B_0$–$B_6$, Main Experiment E1 execution, probe value E2, compute scaling E3, stress tests E4–E5, and resource profiling. | Audits historical numbers and literature claims in `docs/claim_ledger.md`. |

### Rule of Strict Agency Separation (§15.1)
* **Invariant:** An agent or engineer who creates a model, prompt, or dataset split must **never** be the sole agent evaluating or scoring it.
* Pull requests to `main` require explicit sign-off from the designated cross-agent validator.

### Git Branching & Commit Format
Every commit message must follow the convention:
```text
[Update-X][Agent-ID] <Action description> (Refs: §X.X)
```
*Example:* `[Update-1][RA3] Implement reversible Bengali numeral normalizer (Refs: §5.2)`

**Branching Strategy:**
* `main`: Protected production branch.
* `feat/normalizer-verifier`: RA3 engineering branch.
* `feat/benchmark-curation`: RA2 benchmark branch.
* `feat/baselines-eval`: RA4 baseline and evaluation branch.

---

## 4. Phased Milestone Schedule & Upcoming Tasks

The roadmap below preserves the team's intended sequence and deadlines. It is a planning aid, not
evidence that a milestone is complete. The audited current status is maintained in
[`docs/milestones.md`](docs/milestones.md), while the detailed task plan remains in
[`docs/sprint_backlog.md`](docs/sprint_backlog.md).

### Planned roadmap

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GONITSATHI PLANNED ROADMAP                          │
├───────────────┬─────────────────────────────────────────────────────────────┤
│ Update 1      │ Specification, Claim Audit, Core Schemas & Minimal Tests    │
│ (13 Sept)     │ Claim ledger, methodological fixes, schemas, pilot setup    │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ Update 2      │ Normalizer, SymPy Verifier & Baselines B0–B3                │
│ (19 Sept)     │ Core engine, initial dataset ingestion, development trace   │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ Update 3      │ Benchmark Freezing, Disjoint Splits & Adjudication          │
│ (23 Sept)     │ B4–B6 adaptations, annotation, contamination, profiling     │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ Update 4      │ Protocol Freeze, Main Experiment E1 & Ablations A1–A9       │
│ (26 Sept)     │ Frozen thresholds, primary runs, 2x2 factorial tests        │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ Update 5      │ Human Evaluation, Scaling E3 & Stress Tests E4–E5           │
│ (30 Sept)     │ Expert audit, model scaling, perturbations, statistics      │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ Update 6      │ Full Manuscript, Reproducibility Package & Final Gates      │
│ (3 Oct)       │ Paper, figures/tables, release, independent reproduction    │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

### Audited current status

```text
M0  Specification and foundation       IN PROGRESS — external validation open
M1  Coherent and tested core engine    IN PROGRESS — coherence gate open
M2  Pilot benchmark and baselines      IN PROGRESS — benchmark gate open
M3  Protocol freeze and experiments    IN PROGRESS — only preliminary outputs exist
M4  Human/scaling/stress evaluation    IN PROGRESS — only a preliminary profile exists
M5  Manuscript and release             PLANNED
```

Existing Update 2/3 metric reports are preliminary development records, not verified research
results.

### Immediate recovery sequence

1. Fix comparative-run completeness and metric semantics.
2. Complete independent annotation/adjudication, a passing content-level split check, and explicit content hashes.
3. Reconcile controller/config/contract paths and complete missing tests.
4. Tune and freeze the development protocol, register every run, then rerun E1.
5. Generate manuscript claims and tables only from validated registered outputs.

---

## 5. Repository Directory Layout

```text
gonitsathi-oeagent/
├── .agents/                        # Agent configurations (RA1–RA4)
├── .github/workflows/
│   ├── test_engine.yml             # Pytest CI workflow
│   └── lint_and_contracts.yml      # Pydantic schema validation CI
├── configs/
│   ├── thresholds.yaml             # Development thresholds; not protocol-frozen
│   └── prompt_contracts/
│       ├── extractor_contract.json # Appendix B.1 schema
│       └── realizer_contract.json  # Appendix B.2 schema
├── data/
│   ├── raw_bcs/                    # Raw source exam questions
│   ├── benchmark/
│   │   ├── pilot/                  # 28-family constructed development pilot
│   │   ├── train/                  # Placeholder; IDs are currently in manifests
│   │   ├── dev/                    # Placeholder; IDs are currently in manifests
│   │   └── test/                   # Placeholder; IDs are currently in manifests
│   ├── gold_labels/                # Placeholder; adjudicated labels not yet committed
│   └── manifests/                  # Draft ID splits; passing content checks/hashes not recorded
├── docs/
│   ├── README.md                   # Documentation index and map
│   ├── claim_ledger.md             # Inherited metric audit (§2.1)
│   ├── sprint_backlog.md           # Master phased task checklist
│   ├── methodology/                # Methodology specs and literature matrix
│   ├── reports/                    # Guides and preliminary Update 1–3 reports
│   ├── audits/                     # Cross-check and audit logs
│   ├── rubrics/                    # Scoring rubrics
│   └── figures/                    # Benchmark and architecture charts
├── src/
│   ├── normalizer/
│   │   └── bengali_normalizer.py   # Reversible digit & unit normalizer
│   ├── verifier/                   # SymPy & restricted AST checkers
│   ├── controller/
│   │   ├── schemas.py              # Pydantic observation & state contracts
│   │   ├── admission.py            # Evidence filtering & assistance weighting
│   │   ├── belief_model.py         # Categorical belief engine
│   │   ├── probe_selector.py       # Shannon entropy & probe budget cap
│   │   └── workspace.py            # Epistemic workspace coordinator
│   ├── guardrail/                  # Output leakage auditors & fallbacks
│   └── baselines/                  # Implementation of B0 through B6
├── tests/
│   ├── unit/
│   │   └── test_normalizer.py      # Normalizer unit tests
│   └── integration/
│       └── test_minimal_cases.py   # Appendix A.3 minimal verification suite
├── evaluations/
│   ├── comparative/                # Preliminary unregistered comparison summaries
│   ├── profiling/                  # Preliminary five-family CPU-path profile
│   ├── registry/
│   │   └── run_manifest.csv        # Registry schema; currently header-only
│   ├── tables/                     # Placeholder for registered output tables
│   └── logs/                       # Placeholder for registered execution traces
├── requirements.txt                # Pinned dependencies
├── .python-version                 # Pinned Python version (3.11)
├── .gitignore                      # Comprehensive git ignore rules
└── README.md                       # Project documentation
```

---

## Agentic AI Tutoring Runtime

The repository now includes a stateful agentic tutoring runtime built around the evidence-governed diagnostic controller.

The runtime cycle is:

```text
Observe -> Reason -> Plan -> Act -> Reflect -> Repeat
```

Runtime roles:

- `AssessorAgent`: interprets observable student evidence into a strict structured contract.
- `DiagnosticController`: acts as the supervisor and remains the only authority for diagnostic-state updates.
- `ExpertAgent`: realizes only the controller-approved tutoring action in Bengali.
- `CurriculumAgent`: recommends an unseen same-skill or same-topic transfer question.
- `MotivationalAgent`: runs every turn and adds short support only when useful.
- `ModelGateway`: provides one measured local-model interface for agent calls.
- `ResearchBenchmarkRepository`: exposes model-visible benchmark resources while keeping evaluator-only labels outside runtime context.
- `AgenticTutoringOrchestrator`: executes the full loop and records an auditable Observe/Reason/Plan/Act/Reflect trace.

Run the deterministic fallback demo:

```bash
python scripts/run_agentic_demo.py --item BCS10_Q085
```

Run with a downloaded local model:

```bash
python scripts/run_agentic_demo.py --item BCS10_Q085 --model-path /path/to/local/Qwen3-4B
```

Generate a non-interactive smoke trace:

```bash
python scripts/run_agentic_smoke.py
```

The trace is written to `evaluations/logs/agentic_smoke_trace.json`.

Implementation details are in [`docs/agentic_ai_architecture.md`](docs/agentic_ai_architecture.md). A simple mentor/viva explanation is in [`docs/mentor_learning_material.md`](docs/mentor_learning_material.md).
