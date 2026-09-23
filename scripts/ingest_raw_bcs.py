#!/usr/bin/env python3
"""Ingest and curate authentic BCS mathematics examination questions.

Supports ingesting from both:
- Raw directory structure (e.g. ~/Downloads/Data with BCS_questiions.json and BCS_answers.json)
- Historical scraped partitions (bcs_math_questions_*.json and bcs_math_answers_*.json)

Preserves genuine exam metadata, questions, and reference solutions without
fabricating student attempts or private data. Conforms strictly to GonitSathi schemas (§7.3).
"""

from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

# Standardized 6 official BCS math domains defined in project protocol (§7.2)
TOPIC_NORMALIZATION_MAP = {
    "arithmetic": "arithmetic",
    "percentages": "percentage_profit_loss",
    "percentage_profit_loss": "percentage_profit_loss",
    "algebra": "algebra",
    "geometry": "geometry",
    "mensuration": "mensuration",
    "ratios": "ratios_proportions",
    "ratios_proportions": "ratios_proportions",
    "speed_distance": "speed_distance_time",
    "speed_distance_time": "speed_distance_time",
    "work_time": "work_time",
    "number_system": "arithmetic",
    "average_mixture": "arithmetic",
    "mental_ability": "arithmetic",
    "combinatorics": "arithmetic",
}


def normalize_topic(raw_topic: str) -> str:
    cleaned = raw_topic.strip().lower().replace(" ", "_").replace("-", "_")
    return TOPIC_NORMALIZATION_MAP.get(cleaned, "arithmetic")


def extract_exam_tag(source_meta: Any) -> str:
    if isinstance(source_meta, dict):
        exam_str = source_meta.get("exam", "")
        if exam_str:
            match = re.search(r"(\d+)", exam_str)
            if match:
                return f"BCS{int(match.group(1)):02d}"
    return "BCSGEN"


def ingest_bcs_data(source_dir: str, dest_dir: str) -> List[Dict[str, Any]]:
    source_path = Path(os.path.expanduser(source_dir))
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    raw_questions: Dict[str, Dict[str, Any]] = {}
    raw_answers: Dict[str, Dict[str, Any]] = {}

    # Check for direct BCS_questiions.json and BCS_answers.json
    direct_q = source_path / "BCS_questiions.json"
    direct_a = source_path / "BCS_answers.json"

    if direct_q.exists():
        with open(direct_q, "r", encoding="utf-8") as fp:
            items = json.load(fp)
            for item in items:
                raw_id = item.get("family_id")
                if raw_id:
                    raw_questions[raw_id] = item

    if direct_a.exists():
        with open(direct_a, "r", encoding="utf-8") as fp:
            items = json.load(fp)
            for item in items:
                raw_id = item.get("family_id")
                if raw_id:
                    raw_answers[raw_id] = item

    # Also load any partitioned files if present
    question_files = sorted(glob.glob(str(source_path / "bcs_math_questions_*.json")))
    answer_files = sorted(glob.glob(str(source_path / "bcs_math_answers_*.json")))

    for q_file in question_files:
        with open(q_file, "r", encoding="utf-8") as fp:
            items = json.load(fp)
            for item in items:
                raw_id = item.get("family_id")
                if raw_id and raw_id not in raw_questions:
                    raw_questions[raw_id] = item

    for a_file in answer_files:
        with open(a_file, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            items = data["answers"] if isinstance(data, dict) and "answers" in data else data
            for item in items:
                raw_id = item.get("family_id")
                if raw_id and raw_id not in raw_answers:
                    raw_answers[raw_id] = item

    # Standardize and curate problem families
    curated_catalog: List[Dict[str, Any]] = []
    topic_counters: Dict[str, int] = {}

    for raw_id, q in sorted(raw_questions.items()):
        raw_topic = q.get("topic", "arithmetic")
        norm_topic = normalize_topic(raw_topic)
        topic_counters[norm_topic] = topic_counters.get(norm_topic, 0) + 1
        index_in_topic = topic_counters[norm_topic]

        ans_data = raw_answers.get(raw_id, {})
        exam_source = q.get("source") or ans_data.get("source") or {}
        exam_tag = extract_exam_tag(exam_source)

        family_id = f"FAM_{norm_topic.upper()}_{exam_tag}_{index_in_topic:03d}"

        entry: Dict[str, Any] = {
            "family_id": family_id,
            "raw_source_id": raw_id,
            "topic": norm_topic,
            "original_topic_label": raw_topic,
            "subskill": q.get("assigned_subskill", ""),
            "difficulty": q.get("difficulty_rating", "Medium"),
            "question_bn": q.get("question_bn", ""),
            "target_quantity": q.get("target_quantity", ""),
            "answer_options": q.get("answer_options", []),
            "correct_answer": q.get("correct_answer", ""),
            "solution_steps": q.get("solution_steps", []),
            "exam_source": exam_source,
            "annotated_error_catalog": ans_data.get("possible_mistakes", []),
        }
        curated_catalog.append(entry)

    catalog_file = dest_path / "bcs_math_catalog.json"
    with open(catalog_file, "w", encoding="utf-8") as fp:
        json.dump(curated_catalog, fp, indent=2, ensure_ascii=False)

    print(f"Successfully ingested {len(curated_catalog)} authentic BCS problem families.")
    print(f"Saved catalog to: {catalog_file}")
    return curated_catalog


if __name__ == "__main__":
    catalog = ingest_bcs_data("~/Downloads/Data", "data/raw_bcs")
    print(f"Total curated items: {len(catalog)}")
