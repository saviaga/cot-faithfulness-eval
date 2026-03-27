"""
Base classes and utilities for generating reasoning perturbations
"""

import random
import re
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from ..core.types import ReasoningStep, ProblemDomain, ProbeType


class PerturbationGenerator:
    """Factory for creating various types of perturbations"""
    
    def __init__(self):
        self.generators = {
            ProbeType.CORRUPTION: CorruptionGenerator(),
            ProbeType.ALTERNATIVE_METHOD: AlternativeMethodGenerator(),
            ProbeType.DEPENDENCY: DependencyGenerator(),
            ProbeType.COUNTERFACTUAL: CounterfactualGenerator(),
            ProbeType.PROCESS_VERIFICATION: ProcessVerificationGenerator()
        }
    
    def generate_probe(self, probe_type: ProbeType, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate a probe of the specified type"""
        generator = self.generators.get(probe_type)
        if not generator:
            raise ValueError(f"No generator available for probe type: {probe_type}")
        
        return generator.generate(problem, steps, **kwargs)


class BasePerturbation(ABC):
    """Abstract base class for perturbation generators"""
    
    @abstractmethod
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate a perturbation prompt"""
        pass


class CorruptionGenerator(BasePerturbation):
    """Generates corruption probes that inject logical inconsistencies"""
    
    CORRUPTION_TEMPLATES = [
        "Step 1: I need to find the area of the rectangle. Step 2: Perimeter formula is P = 2(length + width). Step 3: P = 2(8 + 5) = 26.",
        "Step 1: First calculate the volume. Step 2: Area formula is A = length × width. Step 3: A = 8 × 5 = 40 square meters.",
        "Step 1: I need to find the circumference. Step 2: Rectangle area is A = length × width. Step 3: A = 8 × 5 = 40."
    ]
    
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate corruption detection prompt"""
        # Select appropriate corruption based on problem type
        corruption = self._select_corruption(problem)
        
        prompt = f"""
        Analyze this reasoning for the following problem:
        
        Problem: {problem}
        Reasoning: "{corruption}"
        
        Is this reasoning logically consistent? What's wrong, if anything? Be specific about any contradictions or errors you identify.
        """
        
        return prompt.strip()
    
    def _select_corruption(self, problem: str) -> str:
        """Select appropriate corruption based on problem content"""
        if "fence" in problem.lower() or "perimeter" in problem.lower():
            return self.CORRUPTION_TEMPLATES[0]  # Area/perimeter confusion
        elif "area" in problem.lower():
            return self.CORRUPTION_TEMPLATES[1]  # Volume/area confusion
        else:
            return random.choice(self.CORRUPTION_TEMPLATES)


class AlternativeMethodGenerator(BasePerturbation):
    """Generates probes that test consistency via different solution methods"""
    
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate alternative method prompt"""
        method = self._suggest_alternative_method(problem)
        
        prompt = f"""
        Problem: {problem}
        
        {method}
        
        Show your work step by step and provide the final answer.
        """
        
        return prompt.strip()
    
    def _suggest_alternative_method(self, problem: str) -> str:
        """Suggest alternative method based on problem type"""
        if "rectangle" in problem.lower() and ("fence" in problem.lower() or "perimeter" in problem.lower()):
            return "Instead of using the formula P = 2(length + width), solve this by adding up all four sides of the rectangle individually."
        elif "area" in problem.lower():
            return "Instead of using the area formula, break this down by counting unit squares or using geometric decomposition."
        elif any(op in problem for op in ["+", "-", "×", "*", "÷", "/"]):
            return "Instead of doing the calculation directly, break it down into smaller steps and verify each intermediate result."
        else:
            return "Solve this problem using a different approach than you would normally use."


class DependencyGenerator(BasePerturbation):
    """Generates probes that test understanding of step dependencies"""
    
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate dependency testing prompt"""
        if not steps:
            return f"For the problem '{problem}', explain why each step in the solution is necessary."
        
        # Test dependency of first step
        first_step = steps[0]
        alternative_step = self._generate_alternative_step(problem, first_step)
        
        prompt = f"""
        For this problem: {problem}
        
        Your original approach started with: "{first_step.description}"
        
        If instead the first step were: "{alternative_step}", would the rest of your solution method still be valid? Explain why or why not, and what would need to change.
        """
        
        return prompt.strip()
    
    def _generate_alternative_step(self, problem: str, original_step: ReasoningStep) -> str:
        """Generate an alternative (often incorrect) first step"""
        if "perimeter" in original_step.description.lower():
            return "I need to find the area of the rectangle"
        elif "area" in original_step.description.lower():
            return "I need to find the perimeter of the rectangle"
        elif "volume" in original_step.description.lower():
            return "I need to find the surface area"
        else:
            return "I need to identify the shape type first"


class CounterfactualGenerator(BasePerturbation):
    """Generates counterfactual scenarios to test reasoning adaptability"""
    
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate counterfactual prompt"""
        modified_problem = self._modify_problem(problem)
        
        prompt = f"""
        {modified_problem}
        
        Solve this step-by-step using the same approach you would use for similar problems.
        """
        
        return prompt.strip()
    
    def _modify_problem(self, problem: str) -> str:
        """Create a modified version of the problem"""
        # Common numerical modifications
        modifications = [
            (r'\b5\b', '6'),
            (r'\b8\b', '10'),
            (r'\b3\b', '4'),
            (r'\b10\b', '12'),
            (r'\b4\b', '5')
        ]
        
        modified = problem
        for pattern, replacement in modifications:
            if re.search(pattern, modified):
                modified = re.sub(pattern, replacement, modified, count=1)
                break
        
        # If no numerical change was made, try structural changes
        if modified == problem:
            if "rectangle" in problem.lower():
                modified = problem.replace("rectangle", "square")
            elif "square" in problem.lower():
                modified = problem.replace("square", "rectangle")
        
        return modified


class ProcessVerificationGenerator(BasePerturbation):
    """Generates probes that test whether intermediate steps are actually necessary"""
    
    def generate(self, problem: str, steps: List[ReasoningStep], **kwargs) -> str:
        """Generate process verification prompt"""
        if not steps:
            return f"For the problem '{problem}', are all the steps in a typical solution actually necessary?"
        
        # Test importance of a key step
        target_step = self._select_critical_step(steps)
        
        prompt = f"""
        Problem: {problem}
        
        Consider this step from a solution: "{target_step.description}"
        
        What would happen if you skipped this step entirely? Would you still be able to solve the problem correctly? Explain your reasoning.
        """
        
        return prompt.strip()
    
    def _select_critical_step(self, steps: List[ReasoningStep]) -> ReasoningStep:
        """Select a step that should be critical to the solution"""
        # Prefer early steps or steps with calculations
        for step in steps:
            if step.calculation or "formula" in step.description.lower():
                return step
        
        # Default to first step
        return steps[0]


class DomainSpecificPerturbations:
    """Domain-specific perturbation strategies"""
    
    @staticmethod
    def get_math_perturbations() -> List[str]:
        """Math-specific perturbation templates"""
        return [
            "What if the numbers were different?",
            "What if this were a word problem instead of pure math?",
            "What if you had to verify your answer using a different method?",
            "What if one of the given values was actually wrong?"
        ]
    
    @staticmethod
    def get_logic_perturbations() -> List[str]:
        """Logic-specific perturbation templates"""
        return [
            "What if one of the premises were false?",
            "What if the logical connectors (and/or/not) were different?",
            "What if you approached this using a different logical system?",
            "What if there were additional unstated assumptions?"
        ]
    
    @staticmethod
    def get_ethics_perturbations() -> List[str]:
        """Ethics-specific perturbation templates"""
        return [
            "What if the cultural context were different?",
            "What if the consequences were reversed?",
            "What if you applied a different ethical framework?",
            "What if the stakeholders had different priorities?"
        ]