"""Evaluation metrics for the diagnostic controller.

Conforms to Section 10.1, 10.2 of GonitSathi Guideline:
- Unsupported-commit risk
- Commitment coverage
- Multiclass Brier score
- First-error accuracy
"""

from typing import Dict, List, Optional
from src.controller.schemas import CandidateCause


def calculate_unsupported_commit_risk(
    active_commitments: List[Dict[str, str]], 
    adjudicated_labels: Dict[str, str]
) -> Optional[float]:
    """
    Calculates unsupported-commit risk.
    Risk = (active commitments not justified by adjudicated evidence) / (all active commitments)
    
    active_commitments: List of dicts with 'learner_id', 'item_id', 'cause' for ACTIVE claims.
    adjudicated_labels: Dict mapping 'learner_id:item_id' -> 'ground_truth_cause'.
    Returns None if no active commitments exist.
    """
    if not active_commitments:
        return None
        
    unsupported_count = 0
    for commit in active_commitments:
        key = f"{commit['learner_id']}:{commit['item_id']}"
        ground_truth = adjudicated_labels.get(key)
        # If the committed cause does not match the adjudicated ground truth, it's an unsupported commit.
        if ground_truth != commit['cause']:
            unsupported_count += 1
            
    return unsupported_count / len(active_commitments)


def calculate_commitment_coverage(
    active_commitments: List[Dict[str, str]], 
    eligible_opportunities: int
) -> float:
    """
    Calculates commitment coverage.
    Coverage = (eligible diagnosis opportunities receiving an active commitment) / (all eligible opportunities)
    """
    if eligible_opportunities <= 0:
        return 0.0
    return len(active_commitments) / eligible_opportunities


def calculate_multiclass_brier_score(
    predictions: List[Dict[CandidateCause, float]], 
    ground_truths: List[CandidateCause]
) -> float:
    """
    Calculates the multiclass Brier score over identifiable cases.
    For each case, sum squared differences between candidate probabilities and the one-hot reference.
    Average over cases; lower is better.
    """
    if not predictions or not ground_truths or len(predictions) != len(ground_truths):
        return 0.0
        
    total_brier = 0.0
    for preds, truth in zip(predictions, ground_truths):
        case_brier = 0.0
        for cause in CandidateCause:
            prob = preds.get(cause, 0.0)
            target = 1.0 if cause == truth else 0.0
            case_brier += (prob - target) ** 2
        total_brier += case_brier
        
    return total_brier / len(predictions)


def calculate_first_error_accuracy(
    predicted_error_steps: List[Optional[str]], 
    ground_truth_steps: List[Optional[str]]
) -> float:
    """
    Exact first-invalid-step match, including a no-error category (None).
    """
    if not predicted_error_steps:
        return 0.0
        
    matches = sum(
        1 for pred, truth in zip(predicted_error_steps, ground_truth_steps) 
        if pred == truth
    )
    return matches / len(predicted_error_steps)
