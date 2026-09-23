"""Baselines module for GonitSathi comparative evaluation (Table 6).

Exposes:
- BaseTutor, BaselineStepResult: Abstract base interface and return contract.
"""

from src.baselines.base import BaseTutor, BaselineStepResult
from src.baselines.b0_rule_template import RuleTemplateTutor
from src.baselines.b1_prompted import PromptedTutor
from src.baselines.b2_verify_then_generate import VerifyThenGenerateTutor
from src.baselines.b3_bayesian import BayesianDiagnosticTutor
from src.baselines.b4_intellicode import IntelliCodeTutor
from src.baselines.b5_scaffoldlm import ScaffoldLMTutor
from src.baselines.b6_slow import SlowWorkspaceTutor
from src.baselines.gonitsathi_adapter import GonitSathiTutor

__all__ = [
    "BaseTutor",
    "BaselineStepResult",
    "RuleTemplateTutor",
    "PromptedTutor",
    "VerifyThenGenerateTutor",
    "BayesianDiagnosticTutor",
    "IntelliCodeTutor",
    "ScaffoldLMTutor",
    "SlowWorkspaceTutor",
    "GonitSathiTutor",
]
