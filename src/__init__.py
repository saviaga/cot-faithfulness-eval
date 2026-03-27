"""
CoT Faithfulness Evaluator

Systematic evaluation of chain-of-thought reasoning faithfulness in large language models.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .evaluators.faithfulness import FaithfulnessEvaluator
from .core.types import (
    FaithfulnessResult,
    FaithfulnessLevel, 
    ProblemDomain,
    ProbeType
)

__all__ = [
    "FaithfulnessEvaluator",
    "FaithfulnessResult", 
    "FaithfulnessLevel",
    "ProblemDomain",
    "ProbeType"
]