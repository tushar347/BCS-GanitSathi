"""Information-Gain Diagnostic Probe Selector.

Conforms to Section 5.6 of GonitSathi Guideline:
- Computes Shannon entropy and Expected Information Gain (EIG).
- Evaluates candidate probes over expert-curated probe bank.
- Enforces strict pedagogical bound: at most 1 probe per problem episode (N_probe <= 1).
- Accounts for response categories including ambiguous, timeout, and incorrect.
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional
from src.controller.schemas import (
    CandidateCause,
    DiagnosticProbe,
)


class ProbeSelector:
    """Selects the optimal diagnostic probe based on expected information gain."""

    def __init__(
        self,
        entropy_threshold: float = 0.40,
        max_probes_per_problem: int = 1,
        burden_penalty_weight: float = 0.05,
    ):
        self.entropy_threshold = entropy_threshold
        self.max_probes_per_problem = max_probes_per_problem
        self.burden_penalty_weight = burden_penalty_weight
        self.probes_asked_in_episode: int = 0

    def reset_episode(self):
        """Resets the probe counter for a new problem episode."""
        self.probes_asked_in_episode = 0

    def calculate_eig(
        self,
        probe: DiagnosticProbe,
        current_beliefs: Dict[CandidateCause, float],
    ) -> float:
        """Calculates Expected Information Gain: EIG = H(C) - E_R[H(C | R)]."""
        # 1. Current Shannon entropy H(C)
        current_entropy = 0.0
        for prob in current_beliefs.values():
            if prob > 1e-9:
                current_entropy -= prob * math.log2(prob)

        # 2. Compute marginal response probabilities P(R = r) = sum_c P(r | c) * P(c)
        marginal_p_r: Dict[str, float] = {}
        for resp_cat, cond_probs in probe.response_model.items():
            p_r = 0.0
            for cause, p_cause in current_beliefs.items():
                p_r_given_c = cond_probs.get(cause, 0.05)  # smoothed
                p_r += p_r_given_c * p_cause
            marginal_p_r[resp_cat] = p_r

        total_p_r = sum(marginal_p_r.values())
        if total_p_r <= 0:
            return 0.0

        # Normalize marginals
        for r in marginal_p_r:
            marginal_p_r[r] /= total_p_r

        # 3. Compute expected posterior entropy E_R[ H(C | R = r) ]
        expected_posterior_entropy = 0.0
        for resp_cat, p_r in marginal_p_r.items():
            if p_r <= 1e-9:
                continue

            cond_probs = probe.response_model[resp_cat]
            # Posterior P(C | R = r)
            posterior_unnorm = {}
            for cause, p_cause in current_beliefs.items():
                p_r_given_c = cond_probs.get(cause, 0.05)
                posterior_unnorm[cause] = p_r_given_c * p_cause

            denom = sum(posterior_unnorm.values())
            h_c_given_r = 0.0
            if denom > 0:
                for cause in current_beliefs:
                    p_c_given_r = posterior_unnorm[cause] / denom
                    if p_c_given_r > 1e-9:
                        h_c_given_r -= p_c_given_r * math.log2(p_c_given_r)

            expected_posterior_entropy += p_r * h_c_given_r

        eig = current_entropy - expected_posterior_entropy
        return max(0.0, eig)

    def select_probe(
        self,
        candidate_probes: List[DiagnosticProbe],
        current_beliefs: Dict[CandidateCause, float],
        normalized_entropy: float,
    ) -> Optional[DiagnosticProbe]:
        """Selects the best probe if uncertainty is high and budget permits."""
        # Hard pedagogical bound: N_probe <= max_probes_per_problem
        if self.probes_asked_in_episode >= self.max_probes_per_problem:
            return None

        # Uncertainty gate: only probe when normalized entropy meets or exceeds threshold
        if normalized_entropy < self.entropy_threshold:
            return None

        best_probe: Optional[DiagnosticProbe] = None
        best_score = -1e9

        for probe in candidate_probes:
            eig = self.calculate_eig(probe, current_beliefs)
            # Subtract normalized time/inference burden penalty
            burden_penalty = self.burden_penalty_weight * (probe.expected_burden_seconds / 60.0)
            score = eig - burden_penalty

            if score > best_score and score > 0:
                best_score = score
                best_probe = probe

        if best_probe is not None:
            self.probes_asked_in_episode += 1

        return best_probe


# Backward-compatibility alias
BoundedProbeSelector = ProbeSelector
