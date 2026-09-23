# GonitSathi Agentic AI Runtime

## Goal

GonitSathi now has a stateful agentic tutoring runtime built around the existing evidence-governed diagnostic controller. The runtime is not a group chat between agents. Every agent has a narrow responsibility and only the diagnostic controller is allowed to authorize learner-state changes.

## Agentic cycle

```text
Student response
    |
    v
OBSERVE
Event + assistance provenance + current problem
    |
    v
REASON
Assessor Agent -> structured interpretation
Normalizer + Symbolic Verifier -> mathematical status
Diagnostic Controller -> competing beliefs
    |
    v
PLAN
Diagnostic Controller chooses one permitted next action
Probe Selector may request one bounded diagnostic response
    |
    v
ACT
Expert Agent realizes the approved teaching action
Curriculum Agent recommends the next independent problem when appropriate
Motivational Agent runs every turn and adds support only when useful
Guardrail audits the final response before release
    |
    v
REFLECT
Actual new student evidence updates beliefs
Uncertainty change and intervention outcome are recorded
Learner memory stores only controller-authorized state
    |
    +-------------------------------> next cycle
```

## Runtime components

| Component | File | Responsibility | Writes diagnostic state |
|---|---|---|---|
| Supervisor / Diagnostic Controller | `src/controller/diagnostic_controller.py` | Evidence admission, belief update, probe/action decision, release audit | Yes |
| Assessor Agent | `src/agents/assessor_agent.py` | Interprets student language into structured observable evidence | No |
| Expert Agent | `src/agents/expert_agent.py` | Produces Bengali tutoring text for the action approved by the controller | No |
| Curriculum Agent | `src/agents/curriculum_agent.py` | Selects an unseen transfer/practice question | No |
| Motivational Agent | `src/agents/motivational_agent.py` | Adds short context-sensitive encouragement | No |
| Model Gateway | `src/models/model_gateway.py` | One shared local-model interface for structured agent calls | No |
| Research Repository | `src/runtime/research_repository.py` | Loads model-visible benchmark records, solutions, probes and output policies | No |
| Session Orchestrator | `src/runtime/session_orchestrator.py` | Runs the cycle and routes information between agents and controller | No independent diagnostic write |
| Learner Memory Store | `src/runtime/learner_memory.py` | Persists snapshots authorized by controller outputs | No inference |

## Information boundaries

The runtime reads `problems.json`, `solutions.json`, `authored_histories_model_visible.json`, `diagnostic_probes.json`, and `output_policies.json`. It does not load `authored_histories_evaluator_only.json` into the student-facing runtime context.

The Assessor Agent receives the current problem, student text, assistance level, and a short visible dialogue history. It returns an interpreted relation, evidence spans, uncertainty, candidate explanations, and clarification need. It cannot activate a learner claim.

The Expert Agent receives only the approved action, permitted facts, recent visible dialogue, and disclosure level. It cannot change diagnosis or reveal a protected final answer.

## Observe

The current student response is recorded with the learner, item, family, assistance level and an independent evidence group. The Assessor Agent tries to convert natural Bengali or mixed-language work into a structured mathematical relation. If a local model is unavailable, a conservative deterministic fallback is used.

## Reason

The Symbolic Verifier checks the interpreted relation against the problem reference. The controller keeps several possible causes instead of turning one wrong answer into a permanent misconception. The belief model distinguishes independent evidence from duplicated evidence and discounts heavily assisted success.

## Plan

The controller chooses an action from the existing action vocabulary. When uncertainty is high and a reviewed probe is available, the Probe Selector can choose one probe under the configured interaction budget. If probing is not appropriate, the controller selects clarification, a conceptual hint, a local scaffold, retry, acknowledgment, transfer, or authorized solution.

## Act

The Expert Agent verbalizes only the approved action. The output policy is checked before release. The guardrail then blocks protected final answers or decisive calculations. The Motivational Agent runs on every turn but stays silent when motivation would add no value.

## Reflect

Reflection is based on actual new evidence, not an LLM imagining what the learner might do. The runtime records uncertainty before and after the observation, whether beliefs changed, the observed outcome, and the next action. Probe responses are classified into the reviewed response categories and then used in a Bayesian belief update.

## Curriculum transition

When a verified final answer completes a problem, the Curriculum Agent searches for an unseen family. It prefers the same subskill when diagnostic evidence suggests the learner needs independent transfer; otherwise it chooses a same-topic progression. The next question is recommended rather than silently counted as mastery.

## Local model use

The model gateway is designed for a local open-weight model. If a model folder is available, set it through `GONITSATHI_MODEL_PATH` or pass `--model-path` to the demo script. The model is loaded with Transformers in deterministic generation mode. If no model is configured, the controller, verifier, probe policy, curriculum and conservative agent fallbacks still run.

Example:

```bash
python scripts/run_agentic_demo.py --item BCS10_Q085 --model-path /path/to/local/Qwen3-4B
```

Without a model:

```bash
python scripts/run_agentic_demo.py --item BCS10_Q085
```

Type `solution` to request an authorized worked solution and `exit` to stop.

## Research-safe design choices

1. One state writer: agents propose evidence or text; the controller governs diagnostic state.
2. Actual evidence: probe updates use the learner's observed response.
3. Bounded probing: the default maximum remains one diagnostic probe per problem.
4. No evaluator-label leakage: evaluator-only histories are not part of runtime context.
5. Assistance-aware evidence: correct work after strong assistance is not treated as independent mastery.
6. Revisable claims: controller hypotheses remain probabilistic and can be contested or retracted.
7. Output release boundary: generated text is audited after the Expert Agent produces it.
8. Cost trace: each turn records neural-call and symbolic-call counts.
9. Explicit cycle record: every turn exposes Observe, Reason, Plan, Act and Reflect fields for auditing.
10. Local-first model interface: model use is optional and measured rather than hidden.
