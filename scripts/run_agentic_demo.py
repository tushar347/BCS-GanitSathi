from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.model_gateway import ModelGateway
from src.runtime.research_repository import ResearchBenchmarkRepository
from src.runtime.session_orchestrator import AgenticTutoringOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", default="BCS10_Q085")
    parser.add_argument("--learner", default="demo_learner")
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--provider", default=None, choices=["fallback", "transformers", "ollama"])
    parser.add_argument("--ollama-model", default=None)
    parser.add_argument("--ollama-url", default=None)
    args = parser.parse_args()
    provider = args.provider or os.getenv("GONITSATHI_MODEL_PROVIDER")
    ollama_model = args.ollama_model or os.getenv("GONITSATHI_OLLAMA_MODEL") or "qwen3:latest"
    ollama_url = args.ollama_url or os.getenv("GONITSATHI_OLLAMA_URL") or "http://localhost:11434"
    repository = ResearchBenchmarkRepository()
    repository.load()
    gateway = ModelGateway(model_path=args.model_path, provider=provider, ollama_model=ollama_model, ollama_url=ollama_url)
    if gateway.provider == "ollama":
        ok, message = gateway.check_ollama_ready()
        if not ok:
            print(message)
            raise SystemExit(1)
    runtime = AgenticTutoringOrchestrator(repository=repository, gateway=gateway)
    runtime.start_session(args.learner, args.item)
    context = repository.get_context(args.item)
    print(context.problem["question_original"])
    if not sys.stdin.isatty():
        return
    while True:
        text = input("Student> ").strip()
        if text.lower() in {"exit", "quit"}:
            break
        if text.lower() == "solution":
            print("Tutor>", runtime.request_worked_solution())
            continue
        result = runtime.submit(text)
        print("Tutor>", result.released_text)
        print("Action>", result.action.action_type.value)
        print("Beliefs>", result.beliefs)
        if result.next_question:
            print("Next>", result.next_question["item_id"], result.next_question["question_original"])


if __name__ == "__main__":
    main()
