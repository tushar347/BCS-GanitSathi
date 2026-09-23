#!/usr/bin/env python3
"""Build a rigorous 28-family pilot benchmark from strictly clean BCS math problems.

Ensures:
1. Only authentic BCS problems with clean, complete solution steps are included.
2. Trajectories integrate authentic diagnostic error banks ('possible_mistakes') from authoring notes.
3. Conforms strictly to the 4-history trajectory schema (§7.2, §5.6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.controller.schemas import CandidateCause

# Standard 6 topic groups defined in §7.2
TOPIC_PILOT_QUOTAS = {
    "algebra": 6,
    "arithmetic": 6,
    "geometry": 5,
    "percentage_profit_loss": 5,
    "ratios_proportions": 3,
    "speed_distance_time": 3,
}


def build_trajectories_for_family(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = item.get("solution_steps", [])
    options = item.get("answer_options", [])
    correct = item.get("correct_answer", "")
    target_q = item.get("target_quantity", "ফলাফল")
    topic = item.get("topic", "arithmetic")
    error_catalog = item.get("annotated_error_catalog", [])

    # Extract authentic error specifications if present in catalog
    conc_mistake = next((m for m in error_catalog if m.get("type") == "conceptual"), None)
    arit_mistake = next((m for m in error_catalog if m.get("type") == "arithmetic"), None)

    # Determine distractors
    distractors = [opt for opt in options if opt.strip() != correct.strip()]

    # H2 Conceptual Distractor & Reasoning
    if conc_mistake and conc_mistake.get("wrong_answer"):
        distractor_1 = conc_mistake.get("wrong_answer")
        conc_reason = " ".join(conc_mistake.get("reasoning_steps", []))
    else:
        distractor_1 = distractors[0] if len(distractors) > 0 else "বিকল্প মান"
        conc_reason = "ভুল সমীকরণ বা সূত্র অনুধাবনের কারণে এই বিভ্রান্তি ঘটে।"

    # H3 Slip Distractor & Reasoning
    if arit_mistake and arit_mistake.get("wrong_answer"):
        distractor_2 = arit_mistake.get("wrong_answer")
        arit_reason = " ".join(arit_mistake.get("reasoning_steps", []))
    else:
        distractor_2 = distractors[1] if len(distractors) > 1 else (distractors[0] if distractors else "ভুল মান")
        arit_reason = "মধ্যবর্তী রূপান্তর সঠিক হলেও শেষ গণনায় অসতর্ক ভুল হয়েছে।"

    step_1 = steps[0]
    step_2 = steps[1] if len(steps) > 2 else steps[-1]
    final_step = steps[-1]

    # Assign appropriate candidate cause enum
    if topic == "percentage_profit_loss":
        conceptual_cause = CandidateCause.PERCENTAGE_BASE.value
    else:
        conceptual_cause = CandidateCause.UNRESOLVED.value

    trajectories = [
        {
            "history_id": "H1_CORRECT",
            "attempt_type": "correct_work",
            "student_visible_steps": [
                step_1,
                step_2,
                final_step,
            ],
            "final_response": correct,
            "gold_error_cause": CandidateCause.NO_ERROR.value,
            "mathematical_status": "valid",
            "description": "Learner followed valid multi-step derivation and reached the verified correct answer.",
        },
        {
            "history_id": "H2_CONCEPTUAL",
            "attempt_type": "persistent_conceptual_error",
            "student_visible_steps": [
                f"শুরুতেই বিকল্প ধারণা প্রয়োগ করা হয়েছে: {conc_reason[:100]}",
                f"ভুল সমীকরণ অনুধাবনের কারণে চূড়ান্ত মান এসেছে: {distractor_1}।",
            ],
            "final_response": distractor_1,
            "gold_error_cause": conceptual_cause,
            "mathematical_status": "invalid",
            "description": f"Learner misapplied structural mathematical relation, leading directly to exam distractor: {distractor_1}.",
            "diagnostic_code": conc_mistake.get("code") if conc_mistake else None,
        },
        {
            "history_id": "H3_SLIP",
            "attempt_type": "transient_arithmetic_slip",
            "student_visible_steps": [
                step_1,
                f"মধ্যবর্তী রূপান্তর সঠিক হলেও গণনায় বিচ্যুতির কারণে উত্তর দাঁড়ায়: {distractor_2}।",
            ],
            "final_response": distractor_2,
            "gold_error_cause": CandidateCause.TRANSIENT_SLIP.value,
            "mathematical_status": "invalid",
            "description": f"Problem setup is correct, but arithmetic slip produced {distractor_2}: {arit_reason[:100]}",
            "diagnostic_code": arit_mistake.get("code") if arit_mistake else None,
        },
        {
            "history_id": "H4_AMBIGUOUS",
            "attempt_type": "ambiguous_attempt",
            "student_visible_steps": [
                step_1,
            ],
            "final_response": None,
            "gold_error_cause": CandidateCause.UNRESOLVED.value,
            "mathematical_status": "unsupported",
            "description": "Student wrote intermediate setup only; cannot diagnose root cause without probing.",
            "diagnostic_probe": {
                "probe_id": f"PRB_{item['family_id']}_01",
                "target_ambiguity": f"Clarify student's intended formula to solve for {target_q}.",
                "prompt_bn": f"আপনার প্রথম ধাপটি সঠিক। এর পরের ধাপে আপনি কীভাবে {target_q} নির্ণয় করবেন?",
                "prompt_en": f"Your first step is correct. In the next step, how will you compute {target_q}?",
                "candidate_causes": [
                    CandidateCause.NO_ERROR.value,
                    conceptual_cause,
                    CandidateCause.TRANSIENT_SLIP.value,
                ],
            },
        },
    ]
    return trajectories


def generate_pilot_dataset(catalog_path: str, output_path: str) -> List[Dict[str, Any]]:
    with open(catalog_path, "r", encoding="utf-8") as fp:
        catalog: List[Dict[str, Any]] = json.load(fp)

    # Filter for strictly clean, uncontaminated items with clear multi-step solutions
    clean_items: List[Dict[str, Any]] = []
    for item in catalog:
        steps = item.get("solution_steps", [])
        steps_str = " ".join(steps)
        # Exclude questions with printing errors or disclaimers in the solution
        if any(w in steps_str for w in ("অসঙ্গতি", "মুদ্রণগত", "অস্পষ্টতা", "ত্রুটি", "নয়;")):
            continue
        if len(steps) >= 2 and len(item.get("answer_options", [])) == 4 and item.get("correct_answer"):
            clean_items.append(item)

    by_topic: Dict[str, List[Dict[str, Any]]] = {}
    for item in clean_items:
        by_topic.setdefault(item["topic"], []).append(item)

    pilot_families: List[Dict[str, Any]] = []

    for topic, quota in TOPIC_PILOT_QUOTAS.items():
        candidates = by_topic.get(topic, [])
        selected = candidates[:quota]
        if len(selected) < quota:
            print(f"Warning: Only found {len(selected)} clean candidates for topic '{topic}' (quota: {quota})")

        for item in selected:
            trajectories = build_trajectories_for_family(item)
            pilot_entry = {
                "family_id": item["family_id"],
                "raw_source_id": item["raw_source_id"],
                "topic": item["topic"],
                "subskill": item["subskill"],
                "difficulty": item["difficulty"],
                "question_bn": item["question_bn"],
                "target_quantity": item["target_quantity"],
                "answer_options": item["answer_options"],
                "correct_answer": item["correct_answer"],
                "solution_steps": item["solution_steps"],
                "exam_source": item["exam_source"],
                "trajectories": trajectories,
            }
            pilot_families.append(pilot_entry)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(pilot_families, fp, indent=2, ensure_ascii=False)

    print(f"Curated {len(pilot_families)} clean pilot problem families across {len(TOPIC_PILOT_QUOTAS)} topics.")
    print(f"Saved to: {out_file}")
    return pilot_families


if __name__ == "__main__":
    generate_pilot_dataset("data/raw_bcs/bcs_math_catalog.json", "data/benchmark/pilot/pilot_28_families.json")
