"""Validate the delivered topic JSON datasets using Python's standard library."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
KEYS = {"family_id", "topic", "in_scope", "assigned_subskill", "difficulty_rating", "target_completion_time", "target_quantity", "english_glossary", "question_bn", "answer_options", "correct_answer", "solution_steps"}

def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def check():
    manifest = load("manifest.json")
    ids = set()
    question_count = mistake_count = 0
    for item in manifest["topic_files"]:
        qs, ans = load(item["questions_file"]), load(item["answers_file"])
        qmap = {q["family_id"]: q for q in qs}
        assert len(qmap) == len(qs), "Duplicate question ID within a topic"
        assert len({a["family_id"] for a in ans}) == len(ans), "Duplicate answer ID"
        assert set(qmap) == {a["family_id"] for a in ans}, "Unmatched question/answer IDs"
        for q in qs:
            assert set(q) == KEYS, (q["family_id"], "Wrong schema")
            assert q["family_id"] not in ids, "Duplicate ID across topics"
            ids.add(q["family_id"])
            assert len(q["answer_options"]) == 4
            assert q["correct_answer"] in q["answer_options"]
            assert q["solution_steps"]
            assert q["difficulty_rating"] in ["Easy", "Medium", "Hard"]
            assert re.fullmatch(r"\d+ seconds", q["target_completion_time"])
            for text in [q["question_bn"], *q["answer_options"]]:
                for path in re.findall(r"\]\(([^)]+\.png)\)", text):
                    assert (ROOT / path).is_file(), (q["family_id"], "Missing image", path)
            question_count += 1
        for a in ans:
            assert a["possible_mistakes"]
            for m in a["possible_mistakes"]:
                assert m["wrong_answer"] != qmap[a["family_id"]]["correct_answer"]
                assert m["reasoning_steps"]
                if m["type"] == "arithmetic":
                    assert 1 <= m["diverges_at_step"] <= len(m["reasoning_steps"])
                mistake_count += 1
    held = load("review_required_questions.json")
    assert not ids.intersection(q["family_id"] for q in held)
    assert all(not q["solution_steps"] for q in held)
    assert question_count == manifest["included_question_count"]
    assert mistake_count == manifest["generated_hypothetical_mistake_count"]
    for path in ROOT.glob("*.json"):
        load(path.name)
    print(f"PASS: {question_count} included questions, {len(held)} held for review, {mistake_count} hypothetical mistake traces.")

if __name__ == "__main__":
    try:
        check()
    except (AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"VALIDATION FAILED: {exc}") from exc
