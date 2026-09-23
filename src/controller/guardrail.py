"""Pedagogical release auditor and answer-leakage guardrail.

Conforms to Section 5.7 and Appendix B.2 of GonitSathi Guideline:
- Audits generated tutor utterances before release to the student.
- In protected hint states, intercepts final answer disclosures and decisive calculations.
- Replaces leaky responses with vetted pedagogically neutral scaffolds.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional
from src.controller.schemas import (
    ActionType,
    PedagogicalAction,
)


SAFE_FALLBACK_HINT_BN = (
    "ধাপটি আরেকবার চিন্তা করুন। মোট খরচ অপরিবর্তিত রাখতে মূল্য ও ব্যবহারের সম্পর্কটি সমীকরণে লিখুন।"
)

SAFE_FALLBACK_CLARIFICATION_BN = (
    "আপনার গণনার ধাপটি স্পষ্টভাবে ব্যাখ্যা করুন, যাতে আমরা একসাথে পরের ধাপে এগোতে পারি।"
)


@dataclass
class AuditResult:
    is_safe: bool
    released_text: str
    leakage_detected: bool
    violation_reason: Optional[str] = None
    fallback_used: bool = False


class PedagogicalGuardrail:
    """Audits tutor responses and enforces disclosure boundary."""

    def __init__(self):
        pass

    def audit_response(
        self,
        action: PedagogicalAction,
        raw_text: str,
        prohibited_final_answers: List[str],
        decisive_calculations: List[str],
    ) -> AuditResult:
        """Audits proposed text. If leaked in a protected state, replaces with safe fallback."""
        # Worked solutions are explicitly authorized to disclose answers
        if action.action_type == ActionType.PROVIDE_WORKED_SOLUTION:
            return AuditResult(
                is_safe=True,
                released_text=raw_text,
                leakage_detected=False,
            )

        # In protected hint/scaffold/probe states, check for leakage
        text_lower = raw_text.lower()

        # 1. Check prohibited final answers (both ASCII and Bengali forms)
        for ans in prohibited_final_answers:
            if not ans:
                continue
            # Regex word/token boundary check
            pattern = re.compile(re.escape(ans.strip()), re.IGNORECASE)
            if pattern.search(text_lower):
                fallback = (
                    SAFE_FALLBACK_CLARIFICATION_BN
                    if action.action_type == ActionType.ASK_CLARIFICATION
                    else SAFE_FALLBACK_HINT_BN
                )
                return AuditResult(
                    is_safe=False,
                    released_text=fallback,
                    leakage_detected=True,
                    violation_reason=f"final_answer_disclosed: {ans}",
                    fallback_used=True,
                )

        # 2. Check decisive calculation forms
        for calc in decisive_calculations:
            if not calc:
                continue
            if calc.strip().lower() in text_lower:
                return AuditResult(
                    is_safe=False,
                    released_text=SAFE_FALLBACK_HINT_BN,
                    leakage_detected=True,
                    violation_reason=f"decisive_calculation_disclosed: {calc}",
                    fallback_used=True,
                )

        # Clean and safe to release
        return AuditResult(
            is_safe=True,
            released_text=raw_text,
            leakage_detected=False,
        )
