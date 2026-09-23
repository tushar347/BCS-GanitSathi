from __future__ import annotations

from typing import Any, Iterable, Mapping

from src.agents.contracts import CurriculumDecision
from src.controller.schemas import CandidateCause


class CurriculumAgent:
    def recommend_next(
        self,
        current_problem: Mapping[str, Any],
        candidate_problems: Iterable[Mapping[str, Any]],
        seen_families: set[str],
        beliefs: Mapping[CandidateCause, float],
    ) -> CurriculumDecision:
        current_family = str(current_problem.get("family_id", ""))
        current_topic = str(current_problem.get("topic_group", ""))
        current_subskill = str(current_problem.get("subskill", ""))
        current_difficulty = str(current_problem.get("difficulty", ""))
        ranked = []
        top_error = max(
            ((cause, prob) for cause, prob in beliefs.items() if cause != CandidateCause.NO_ERROR),
            key=lambda x: x[1],
            default=(CandidateCause.UNRESOLVED, 0.0),
        )
        for problem in candidate_problems:
            family_id = str(problem.get("family_id", ""))
            if not family_id or family_id == current_family or family_id in seen_families:
                continue
            if not problem.get("in_scope", True):
                continue
            score = 0
            if problem.get("topic_group") == current_topic:
                score += 6
            if problem.get("subskill") == current_subskill:
                score += 5
            if str(problem.get("difficulty", "")) == current_difficulty:
                score += 2
            if top_error[1] >= 0.5 and problem.get("subskill") == current_subskill:
                score += 4
            ranked.append((score, str(problem.get("item_id", "")), problem))
        if not ranked:
            return CurriculumDecision(action="end_or_expand_scope", reason_code="no_unseen_in_scope_candidate")
        ranked.sort(key=lambda x: (-x[0], x[1]))
        chosen = ranked[0][2]
        return CurriculumDecision(
            action="offer_transfer_question" if top_error[1] >= 0.5 else "next_practice_question",
            item_id=str(chosen.get("item_id", "")),
            family_id=str(chosen.get("family_id", "")),
            topic_group=str(chosen.get("topic_group", "")),
            subskill=str(chosen.get("subskill", "")),
            difficulty=str(chosen.get("difficulty", "")),
            reason_code="same_subskill_independent_transfer" if chosen.get("subskill") == current_subskill else "same_topic_progression",
        )
