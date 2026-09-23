# How I Built GonitSathi Agentic AI

## One-sentence explanation

I converted GonitSathi from a normal question-answer tutor into a stateful agentic tutoring loop where specialized agents observe the student's work, the central controller reasons over verified evidence, plans the next action, executes it through a teaching agent, and then reflects on the student's next real response.

## The easiest flow to remember

```text
Observe -> Reason -> Plan -> Act -> Reflect -> Repeat
```

## What I should tell my mentor

GonitSathi already had a Bengali normalizer, symbolic math verifier, evidence admission, Bayesian diagnostic belief, probe selector and output guardrail. I kept these because they make the system auditable. I did not replace them with one large chatbot.

Then I added four tutoring agents around the controller.

The Assessor Agent reads the student's Bengali or mixed-language answer and extracts structured evidence. It does not decide permanent learner state.

The Expert Agent explains or gives a hint only after the controller chooses the action. It cannot freely reveal the answer.

The Curriculum Agent selects the next unseen BCS question, especially a related transfer question when we need independent evidence of learning.

The Motivational Agent runs every turn, but it speaks only when encouragement is useful, such as repeated mistakes or recovery after difficulty.

The Diagnostic Controller acts as the supervisor. It is the only component that can authorize diagnostic state updates. It uses the symbolic verifier, evidence admission, belief updater, probe selector and guardrail as tools.

## A simple example

Suppose the correct answer is 10 and the student answers 11.

1. Observe: the system records `11` and whether the student had help.
2. Reason: the Assessor converts it to `answer = 11`; the symbolic verifier marks it invalid; the controller keeps multiple possible causes instead of claiming one misconception immediately.
3. Plan: because the diagnosis is uncertain, the controller selects one diagnostic probe.
4. Act: the Expert Agent asks the approved probe without revealing the answer.
5. Reflect: the student's actual probe response changes the probability of the competing diagnoses.
6. Repeat: the controller now gives a hint, requests a retry, or moves to another question depending on the new evidence.

If the student later answers a related question correctly without help, that independent evidence can weaken or retract the earlier error claim.

## Why this is agentic and not just a chatbot

A chatbot usually receives a message and generates one response. GonitSathi keeps state, chooses between tools and agents, changes its plan from new evidence, limits its own actions using policies, and repeats the loop until the learning episode changes state.

The important part is not simply having many agents. The important part is that the next action depends on observed evidence and the system can revise its earlier belief.

## Why I used a central controller

If every agent could directly edit learner state, one model mistake could become a permanent diagnosis. I therefore used a single-writer design. Agents can propose interpretations or responses, but the controller owns evidence admission and learner-state authorization.

## Tools used

- Python for the runtime
- Pydantic for strict structured agent contracts
- SymPy for verified mathematical checking
- Transformers for an optional local open-weight model
- Qwen-compatible local model interface through the shared Model Gateway
- JSON research benchmark files for problems, solutions, histories, probes and policies
- Pytest for unit and integration testing

## Main files I added

```text
src/agents/assessor_agent.py
src/agents/expert_agent.py
src/agents/curriculum_agent.py
src/agents/motivational_agent.py
src/models/model_gateway.py
src/runtime/research_repository.py
src/runtime/session_state.py
src/runtime/session_orchestrator.py
src/runtime/learner_memory.py
scripts/run_agentic_demo.py
```

## What happens when there is no LLM model loaded

The system does not break. It uses conservative deterministic fallbacks for interpretation and response wording while the symbolic verifier, controller, probing, state update, curriculum and guardrail continue to work. When a local model is configured, the Assessor and Expert use that model through the same gateway.

## What I did not allow

I did not allow agents to read evaluator-only labels during tutoring. I did not allow the Expert Agent to update diagnostic state. I did not let a single wrong answer become a permanent misconception. I did not use simulated probe responses to update real learner state. I did not allow protected hints to reveal final answers.

## 30-second viva answer

I built GonitSathi as an evidence-governed multi-agent tutoring system. The loop is Observe, Reason, Plan, Act and Reflect. An Assessor Agent interprets the student's work, the symbolic verifier checks the math, and a central Diagnostic Controller updates competing beliefs and selects the next action. An Expert Agent teaches, a Curriculum Agent selects the next problem, and a Motivational Agent supports engagement. After the student's next real response, the system reflects, updates its state and repeats the cycle.

## 2-minute mentor explanation

My project is not a normal chatbot. I first kept the existing deterministic components, especially the Bengali normalizer, SymPy verifier, evidence admission, Bayesian belief model, diagnostic probe selector and output guardrail. Then I built an agent layer around them. The Assessor Agent handles natural-language interpretation, but it only returns structured evidence. The Diagnostic Controller is the supervisor and the only authorized writer of diagnostic state. It decides whether the system needs clarification, one diagnostic probe, a hint, a scaffold, a retry or another problem. The Expert Agent turns that approved action into natural Bengali, and the guardrail checks it before the student sees it. The Curriculum Agent selects an independent transfer question when the student is ready, and the Motivational Agent runs every turn but only speaks when useful. Finally, the runtime compares the new evidence with the previous belief, records the uncertainty change, and starts the next cycle. This makes the system agentic because its next action changes from real observations rather than following a fixed prompt sequence.

## Questions my mentor may ask

### Why not let the LLM do everything?

Because mathematical correctness and learner-state diagnosis need auditable evidence. I use the LLM where language understanding and natural explanation are useful, but SymPy and the controller handle verifiable decisions.

### Why multiple agents?

The agents have different responsibilities and permissions. This reduces prompt complexity and makes it possible to measure which component caused a decision.

### Why is the controller the only state writer?

It prevents an Assessor or Expert hallucination from directly becoming a persistent learner diagnosis.

### What makes the loop agentic?

The system observes a new event, chooses a state-dependent tool or agent, receives new evidence, updates its belief, reflects on the result and changes the next action.

### How do diagnostic probes work?

When several explanations are still possible, the controller can ask one reviewed short question. The student's actual response is classified into a response category and updates the competing beliefs. The probe is limited so the tutor does not keep questioning the learner unnecessarily.

### What is reflection here?

Reflection is not hidden free-form self-talk. It is a measurable record of what new evidence arrived, whether uncertainty decreased, whether the diagnostic state changed and which next action was selected.

### How do I use a real model?

Download a supported local model, install the project dependencies, then run the demo with `--model-path`. The shared Model Gateway sends structured calls to the Assessor and Expert so model use is controlled and countable.
