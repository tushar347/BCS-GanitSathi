from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.runtime.research_repository import ResearchBenchmarkRepository
from src.runtime.session_orchestrator import AgenticTutoringOrchestrator


def main() -> None:
    repository = ResearchBenchmarkRepository()
    repository.load()
    runtime = AgenticTutoringOrchestrator(repository=repository)
    runtime.start_session("smoke_learner", "BCS10_Q085")
    first = runtime.submit("11")
    turns = [first.cycle.model_dump(mode="json")]
    if first.session.pending_probe is not None:
        second = runtime.submit("insufficient_evidence")
        turns.append(second.cycle.model_dump(mode="json"))
    output = {
        "research_runtime_problem_count": len(repository.list_problems()),
        "item_id": "BCS10_Q085",
        "turns": turns,
        "learner_memory": runtime.memory.get("smoke_learner").model_dump(mode="json"),
    }
    target = Path("evaluations/logs/agentic_smoke_trace.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
