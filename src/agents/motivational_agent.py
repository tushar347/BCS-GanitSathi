from __future__ import annotations

from src.agents.contracts import MotivationDecision
from src.controller.schemas import MathematicalStatus


class MotivationalAgent:
    def decide(
        self,
        mathematical_status: MathematicalStatus,
        consecutive_errors: int,
        consecutive_successes: int,
        recovered_after_help: bool,
    ) -> MotivationDecision:
        if recovered_after_help and mathematical_status == MathematicalStatus.VALID:
            return MotivationDecision(
                should_include=True,
                mode="recovery",
                message="ভালো অগ্রগতি। এবার একই ধারণা নতুন প্রশ্নে নিজে প্রয়োগ করে দেখো।",
            )
        if consecutive_errors >= 2:
            return MotivationDecision(
                should_include=True,
                mode="support",
                message="একই জায়গায় কয়েকবার আটকে গেছ। ছোট একটি ধাপ ধরে আবার চেষ্টা করি।",
            )
        if consecutive_successes >= 3:
            return MotivationDecision(
                should_include=True,
                mode="challenge",
                message="তুমি ধারাবাহিকভাবে সঠিক করছ। এবার একটু বেশি চ্যালেঞ্জিং প্রশ্ন নেওয়া যায়।",
            )
        return MotivationDecision(should_include=False, mode="silent", message="")
