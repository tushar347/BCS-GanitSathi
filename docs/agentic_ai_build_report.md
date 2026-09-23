# Agentic AI Build Report

## Implemented

The current codebase was extended with a complete stateful agentic tutoring path without replacing the evidence-governed controller.

### New runtime packages

```text
src/agents/
src/models/
src/runtime/
```

### New agents

```text
AssessorAgent
ExpertAgent
CurriculumAgent
MotivationalAgent
```

The existing `DiagnosticController` is the supervisor/controller. It keeps exclusive authority over evidence admission, diagnostic beliefs, probe selection, action authorization and release auditing.

### New agentic loop

Each runtime turn records:

```text
Observe
Reason
Plan
Act
Reflect
```

The cycle record is returned in `AgenticTurnResult.cycle` and is also suitable for experiment logging.

### Actual probe-response reflection

The previous controller could select a diagnostic probe. The runtime now also handles the student's real probe response, classifies it into a probe response category, updates the Bayesian diagnostic distribution from that observed response and records whether uncertainty changed.

### Structured local-model gateway

`ModelGateway` provides one shared model boundary for the Assessor and Expert. A callable backend can be injected in tests. A local Hugging Face model can be loaded through a local path. No external API is required by the implementation.

### Research benchmark integration

`ResearchBenchmarkRepository` reads only student-facing research resources:

```text
problems.json
solutions.json
authored_histories_model_visible.json
diagnostic_probes.json
output_policies.json
```

Evaluator-only histories are not included in `RuntimeProblemContext`.

### Final-answer verification

`ProblemReferenceDAG` now supports `accepted_answer_forms`. The symbolic verifier can validate accepted final answer forms before normal symbolic step comparison.

### Learner memory

`LearnerMemoryStore` persists controller-authorized snapshots of turns, completion and claim states. The teaching agents do not write this state directly.

### Output policy and guardrail

The orchestrator enforces the item's output policy before the Expert Agent response is released. The existing pedagogical guardrail audits the realized response for protected final-answer disclosure.

### Curriculum and motivation

A completed final answer can invoke the Curriculum Agent to recommend an unseen transfer/practice question. The Motivational Agent runs every turn but stays silent unless support, recovery or challenge messaging is useful.

## Validation

The full Pytest suite passes after the integration.

```text
118 passed
```

The agentic smoke run produced `evaluations/logs/agentic_smoke_trace.json` and exercised:

```text
wrong answer
-> evidence update
-> diagnostic probe
-> actual probe response
-> belief update
-> reflection
-> next teaching action
```

The repository-wide verification script cannot fully pass in this execution container because the container uses Python 3.13 while the project intentionally pins Python 3.11, and the container does not have the development packages `ruff` and `transformers` installed or Git metadata from the original repository. Syntax compilation, configuration/schema parsing, source imports and Pytest pass in the current workspace.
