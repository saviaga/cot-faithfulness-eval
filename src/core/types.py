"""
Core type definitions for CoT Faithfulness Evaluator
"""

from typing import Dict, List, Optional, Union, Any, Literal
from dataclasses import dataclass
from enum import Enum
import json


class FaithfulnessLevel(Enum):
    """Faithfulness assessment levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"


class ProbeType(Enum):
    """Types of consistency probes"""
    CORRUPTION = "corruption"
    ALTERNATIVE_METHOD = "alternative_method"
    DEPENDENCY = "dependency"
    COUNTERFACTUAL = "counterfactual"
    PROCESS_VERIFICATION = "process_verification"


class ProblemDomain(Enum):
    """Problem domains for evaluation"""
    MATH = "math"
    LOGIC = "logic"
    ETHICS = "ethics"
    CODE = "code"
    SCIENCE = "science"


@dataclass
class ReasoningStep:
    """Individual step in chain-of-thought reasoning"""
    step_number: int
    description: str
    calculation: Optional[str] = None
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "description": self.description,
            "calculation": self.calculation,
            "confidence": self.confidence
        }


@dataclass
class ProbeResult:
    """Result from a single consistency probe"""
    probe_type: ProbeType
    prompt: str
    response: str
    passed: bool
    confidence: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "probe_type": self.probe_type.value,
            "prompt": self.prompt,
            "response": self.response,
            "passed": self.passed,
            "confidence": self.confidence,
            "details": self.details
        }


@dataclass
class FaithfulnessResult:
    """Complete faithfulness evaluation result"""
    problem: str
    domain: ProblemDomain
    original_response: str
    reasoning_steps: List[ReasoningStep]
    probe_results: List[ProbeResult]
    consistency_score: int  # 0-100
    faithfulness_level: FaithfulnessLevel
    analysis_details: Dict[str, Any]
    model_name: str
    timestamp: str
    
    @property
    def passed_probes(self) -> int:
        """Number of probes that passed"""
        return sum(1 for probe in self.probe_results if probe.passed)
    
    @property
    def total_probes(self) -> int:
        """Total number of probes run"""
        return len(self.probe_results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "domain": self.domain.value,
            "original_response": self.original_response,
            "reasoning_steps": [step.to_dict() for step in self.reasoning_steps],
            "probe_results": [probe.to_dict() for probe in self.probe_results],
            "consistency_score": self.consistency_score,
            "faithfulness_level": self.faithfulness_level.value,
            "analysis_details": self.analysis_details,
            "model_name": self.model_name,
            "timestamp": self.timestamp,
            "passed_probes": self.passed_probes,
            "total_probes": self.total_probes
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class EvaluationConfig:
    """Configuration for faithfulness evaluation"""
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 800
    timeout: int = 30
    rate_limit_delay: float = 1.0
    retry_attempts: int = 3
    probe_types: List[ProbeType] = None
    
    def __post_init__(self):
        if self.probe_types is None:
            self.probe_types = list(ProbeType)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark evaluation"""
    models: List[str]
    domains: List[ProblemDomain]
    num_problems: int = 100
    output_dir: str = "data/results"
    parallel_requests: int = 5
    save_intermediate: bool = True
    
    def __post_init__(self):
        if not self.domains:
            self.domains = list(ProblemDomain)


@dataclass
class Problem:
    """Individual problem for evaluation"""
    id: str
    text: str
    domain: ProblemDomain
    expected_answer: Optional[str] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "domain": self.domain.value,
            "expected_answer": self.expected_answer,
            "difficulty": self.difficulty,
            "metadata": self.metadata or {}
        }


@dataclass
class ModelInfo:
    """Information about a model being evaluated"""
    name: str
    provider: str  # openai, anthropic, etc.
    version: Optional[str] = None
    context_length: Optional[int] = None
    cost_per_token: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider,
            "version": self.version,
            "context_length": self.context_length,
            "cost_per_token": self.cost_per_token
        }