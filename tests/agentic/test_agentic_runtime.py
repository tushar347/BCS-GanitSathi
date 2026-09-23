import json

from src.agents.assessor_agent import AssessorAgent
from src.agents.contracts import AssessmentResult
from src.controller.prompt_contracts import ExtractorOutputContract, RealizerOutputContract
from src.controller.belief_updater import CalibratedBeliefUpdater
from src.controller.schemas import ActionType, AssistanceLevel, CandidateCause, MathematicalStatus
from src.models.model_gateway import ModelGateway
from src.runtime.research_repository import ResearchBenchmarkRepository
from src.runtime.session_orchestrator import AgenticTutoringOrchestrator


def test_gateway_validates_structured_callable():
    def backend(system_prompt, user_prompt):
        return {
            "interpreted_relation": "answer = 10",
            "evidence_spans": ["10"],
            "interpretation_uncertainty": 0.0,
            "candidate_explanations": ["no_error"],
            "assistance_references": [],
            "needs_clarification": False,
            "is_final_answer": True,
            "reason_codes": ["explicit_answer"],
        }

    gateway = ModelGateway(callable_backend=backend)
    assessor = AssessorAgent(gateway)
    result = assessor.assess("question", "10", AssistanceLevel.NONE)
    assert result.interpreted_relation == "answer = 10"
    assert assessor.last_used_model is True
    assert gateway.call_count == 1


def test_repository_uses_only_model_visible_runtime_records():
    repository = ResearchBenchmarkRepository()
    count = repository.load()
    assert count > 0
    context = repository.get_context("BCS10_Q085")
    dumped = context.model_dump()
    assert "evaluator" not in json.dumps(dumped, ensure_ascii=False).lower()
    assert context.problem["topic_group"] == "elementary_algebra_number_relations"


def test_repository_builds_final_answer_dag():
    repository = ResearchBenchmarkRepository()
    repository.load()
    dag = repository.build_problem_dag("BCS10_Q085")
    assert "10" in dag.accepted_answer_forms
    assert any(step.step_id == "final_answer" for step in dag.reference_steps)


def test_agentic_runtime_correct_answer_invokes_curriculum():
    repository = ResearchBenchmarkRepository()
    repository.load()
    runtime = AgenticTutoringOrchestrator(repository=repository)
    runtime.start_session("learner_test", "BCS10_Q085")
    result = runtime.submit("10")
    assert result.observation["mathematical_status"] == MathematicalStatus.VALID.value
    assert result.action.action_type == ActionType.ACKNOWLEDGE_CORRECT_STEP
    assert result.curriculum is not None
    assert result.curriculum.item_id is not None
    assert result.next_question is not None
    assert result.trace.motivation_invoked is True


def test_agentic_runtime_observe_plan_act_reflect_probe_loop():
    repository = ResearchBenchmarkRepository()
    repository.load()
    runtime = AgenticTutoringOrchestrator(repository=repository)
    runtime.start_session("learner_probe", "BCS10_Q085")
    first = runtime.submit("11")
    assert first.action.action_type == ActionType.ASK_DIAGNOSTIC_PROBE
    assert first.session.pending_probe is not None
    before = dict(first.beliefs)
    second = runtime.submit("insufficient_evidence")
    assert second.session.pending_probe is None
    assert second.trace.probe_response_category == "insufficient_evidence"
    assert second.beliefs != before
    assert second.action.action_type != ActionType.ASK_DIAGNOSTIC_PROBE


def test_agentic_runtime_clarification_questions_do_not_update_beliefs():
    repository = ResearchBenchmarkRepository()
    repository.load()
    runtime = AgenticTutoringOrchestrator(repository=repository)
    runtime.start_session("learner_clarify", "BCS10_Q085")
    first = runtime.submit("10")
    before = dict(first.beliefs)
    second = runtime.submit("১ কি মৌলিক সংখ্যা?")
    assert second.observation["event_type"] == "clarification_question"
    assert second.action.action_type == ActionType.ASK_CLARIFICATION
    assert second.beliefs == before
    assert second.trace.reason_codes == ["clarification_question"]


def test_contextual_belief_priors_exclude_percentage_base_for_prime_questions():
    updater = CalibratedBeliefUpdater()
    updater.set_problem_context(problem_text="নিচের কোনটি মৌলিক সংখ্যা?", topic_group="prime_number_identification")
    assert updater.priors[CandidateCause.PERCENTAGE_BASE] == 0.0
    assert sum(updater.priors.values()) == 1.0

    updater.set_problem_context(problem_text="একটি পণ্যের মূল্য ২০% বৃদ্ধি পেল।", topic_group="percentages_profit_loss")
    assert updater.priors[CandidateCause.PERCENTAGE_BASE] > 0.1


def test_prompt_contract_files_match_runtime_contract_fields():
    extractor = json.loads(open("configs/prompt_contracts/extractor_contract.json", encoding="utf-8").read())
    realizer = json.loads(open("configs/prompt_contracts/realizer_contract.json", encoding="utf-8").read())
    assert set(extractor["properties"]) == set(ExtractorOutputContract.model_fields)
    assert set(realizer["properties"]) == set(RealizerOutputContract.model_fields)


def test_ollama_provider_configuration_from_environment(monkeypatch):
    monkeypatch.setenv("GONITSATHI_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("GONITSATHI_OLLAMA_MODEL", "qwen3:latest")
    monkeypatch.setenv("GONITSATHI_OLLAMA_URL", "http://localhost:11434")
    monkeypatch.delenv("GONITSATHI_MODEL_PATH", raising=False)

    gateway = ModelGateway()

    assert gateway.provider == "ollama"
    assert gateway.ollama_model == "qwen3:latest"
    assert gateway.ollama_url == "http://localhost:11434"


def test_ollama_generation_uses_expected_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload
            self.status = 200

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request):
        captured["method"] = request.get_method()
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({
            "response": "{\"interpreted_relation\":\"answer = 10\",\"evidence_spans\":[\"10\"],\"interpretation_uncertainty\":0.0,\"candidate_explanations\":[\"no_error\"],\"assistance_references\":[],\"needs_clarification\":false,\"is_final_answer\":true,\"reason_codes\":[\"explicit_answer\"]}",
            "prompt_eval_count": 12,
            "eval_count": 20,
            "total_duration": 1234567,
            "load_duration": 100000,
        })

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    gateway = ModelGateway(provider="ollama", ollama_model="qwen3:latest", ollama_url="http://localhost:11434", max_new_tokens=64)

    result = gateway.generate_text("system", "user")

    assert result.startswith("{\"")
    assert captured["method"] == "POST"
    assert captured["body"]["model"] == "qwen3:latest"
    assert captured["body"]["stream"] is False
    assert captured["body"]["think"] is False
    assert captured["body"]["options"]["temperature"] == 0
    assert captured["body"]["options"]["num_predict"] == 64
    assert gateway.call_count == 1
    assert gateway.last_call_metadata["provider"] == "ollama"
    assert gateway.last_call_metadata["model"] == "qwen3:latest"
    assert gateway.last_call_metadata["prompt_tokens"] == 12
    assert gateway.last_call_metadata["generated_tokens"] == 20
    assert gateway.last_call_metadata["status"] == "success"


def test_gateway_rejects_malformed_structured_output(monkeypatch):
    def backend(system_prompt, user_prompt):
        return "not-json"

    gateway = ModelGateway(callable_backend=backend)
    result = gateway.generate_structured("system", "user", AssessmentResult)

    assert result is None


def test_gateway_rejects_pydantic_mismatch(monkeypatch):
    def backend(system_prompt, user_prompt):
        return {"interpreted_relation": 42, "evidence_spans": ["ok"]}

    gateway = ModelGateway(callable_backend=backend)
    result = gateway.generate_structured("system", "user", AssessmentResult)

    assert result is None


def test_run_agentic_demo_cli_overrides_environment(monkeypatch):
    import sys
    from unittest.mock import patch

    monkeypatch.setenv("GONITSATHI_MODEL_PROVIDER", "fallback")
    monkeypatch.setenv("GONITSATHI_OLLAMA_MODEL", "other-model")
    monkeypatch.setenv("GONITSATHI_OLLAMA_URL", "http://example.invalid")
    argv = [
        "run_agentic_demo.py",
        "--item",
        "BCS10_Q085",
        "--provider",
        "ollama",
        "--ollama-model",
        "qwen3:latest",
        "--ollama-url",
        "http://localhost:11434",
    ]
    with patch.object(sys, "argv", argv), patch("scripts.run_agentic_demo.ModelGateway") as gateway_cls, patch("scripts.run_agentic_demo.AgenticTutoringOrchestrator") as runtime_cls, patch("scripts.run_agentic_demo.ResearchBenchmarkRepository") as repo_cls:
        repo = repo_cls.return_value
        repo.load.return_value = 1
        repo.get_context.return_value.problem = {"question_original": "Q"}
        runtime = runtime_cls.return_value
        runtime.start_session.return_value = None
        runtime.request_worked_solution.return_value = "done"
        runtime.submit.return_value = type("Result", (), {"released_text": "hi", "action": type("Action", (), {"action_type": type("T", (), {"value": "ack"})()})(), "beliefs": {}, "next_question": None})()

        import scripts.run_agentic_demo as demo
        demo.main()

    gateway_cls.assert_called_once_with(model_path=None, provider="ollama", ollama_model="qwen3:latest", ollama_url="http://localhost:11434")
