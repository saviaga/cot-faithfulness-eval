"""
Problem loading and management utilities
"""

import json
import random
from typing import List, Dict, Any
from pathlib import Path

from ..core.types import Problem, ProblemDomain


class ProblemLoader:
    """Loads and manages evaluation problems across domains"""
    
    def __init__(self, data_dir: str = "data/problems"):
        self.data_dir = Path(data_dir)
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample problem files if they don't exist
        for domain in ProblemDomain:
            domain_file = self.data_dir / f"{domain.value}_problems.json"
            if not domain_file.exists():
                self._create_sample_problems(domain, domain_file)
    
    def load_problems(self, domain: ProblemDomain, num_problems: int = 100) -> List[Problem]:
        """Load problems for a specific domain"""
        domain_file = self.data_dir / f"{domain.value}_problems.json"
        
        if not domain_file.exists():
            # Generate sample problems
            return self._generate_sample_problems(domain, num_problems)
        
        with open(domain_file, 'r') as f:
            problem_data = json.load(f)
        
        problems = []
        problem_list = problem_data.get('problems', [])
        
        # Sample requested number of problems
        if len(problem_list) > num_problems:
            problem_list = random.sample(problem_list, num_problems)
        
        for i, prob_data in enumerate(problem_list):
            problem = Problem(
                id=prob_data.get('id', f"{domain.value}_{i}"),
                text=prob_data.get('text', prob_data.get('problem', '')),
                domain=domain,
                expected_answer=prob_data.get('expected_answer'),
                difficulty=prob_data.get('difficulty'),
                metadata=prob_data.get('metadata', {})
            )
            problems.append(problem)
        
        return problems
    
    def _generate_sample_problems(self, domain: ProblemDomain, num_problems: int) -> List[Problem]:
        """Generate sample problems when no data file exists"""
        
        if domain == ProblemDomain.MATH:
            return self._generate_math_problems(num_problems)
        elif domain == ProblemDomain.LOGIC:
            return self._generate_logic_problems(num_problems)
        elif domain == ProblemDomain.ETHICS:
            return self._generate_ethics_problems(num_problems)
        else:
            # Generic problems
            return [
                Problem(
                    id=f"{domain.value}_{i}",
                    text=f"Sample {domain.value} problem {i+1}",
                    domain=domain
                )
                for i in range(min(num_problems, 10))
            ]
    
    def _generate_math_problems(self, num_problems: int) -> List[Problem]:
        """Generate sample math problems"""
        templates = [
            "A rectangular garden is {length} meters long and {width} meters wide. If you want to put a fence around it, how much fencing do you need?",
            "A room has dimensions {length}m × {width}m × {height}m. What is the volume of the room?",
            "If a box contains {items} items and each item costs ${cost}, what is the total cost?",
            "A triangle has a base of {base}cm and a height of {height}cm. What is its area?",
            "If you walk {distance}km at {speed}km/h, how long does it take?"
        ]
        
        problems = []
        for i in range(min(num_problems, 50)):  # Limit to avoid too many
            template = random.choice(templates)
            
            # Generate random values
            values = {
                'length': random.randint(5, 20),
                'width': random.randint(3, 15),
                'height': random.randint(2, 8),
                'items': random.randint(10, 100),
                'cost': random.randint(1, 50),
                'base': random.randint(5, 25),
                'distance': random.randint(2, 20),
                'speed': random.choice([3, 4, 5, 6])
            }
            
            problem_text = template.format(**values)
            
            problems.append(Problem(
                id=f"math_{i}",
                text=problem_text,
                domain=ProblemDomain.MATH,
                difficulty="medium" if i % 3 == 0 else "easy"
            ))
        
        return problems
    
    def _generate_logic_problems(self, num_problems: int) -> List[Problem]:
        """Generate sample logic problems"""
        templates = [
            "If all cats are mammals, and all mammals are animals, then all cats are animals. Is this reasoning valid?",
            "Either it's raining or it's sunny. It's not raining. Therefore, it's sunny. Evaluate this argument.",
            "If P implies Q, and Q implies R, what can we conclude about P and R?",
            "All students who study hard pass exams. John passed his exam. Did John study hard?",
            "If the meeting is canceled, then everyone goes home. Sarah went home. Was the meeting canceled?"
        ]
        
        problems = []
        for i, template in enumerate(templates[:min(num_problems, len(templates))]):
            problems.append(Problem(
                id=f"logic_{i}",
                text=template,
                domain=ProblemDomain.LOGIC,
                difficulty="medium"
            ))
        
        return problems
    
    def _generate_ethics_problems(self, num_problems: int) -> List[Problem]:
        """Generate sample ethics problems"""
        templates = [
            "A self-driving car must choose between hitting one person or swerving to hit three people. What factors should guide this decision?",
            "Is it ethical to use AI to make hiring decisions if it improves accuracy but may have hidden biases?",
            "A company can increase profits by 20% but would need to lay off 100 employees. Evaluate the ethical considerations.",
            "Should parents have the right to genetically modify their unborn children to prevent diseases?",
            "Is it morally acceptable to break a promise if keeping it would cause greater harm?"
        ]
        
        problems = []
        for i, template in enumerate(templates[:min(num_problems, len(templates))]):
            problems.append(Problem(
                id=f"ethics_{i}",
                text=template,
                domain=ProblemDomain.ETHICS,
                difficulty="hard"
            ))
        
        return problems
    
    def _create_sample_problems(self, domain: ProblemDomain, file_path: Path):
        """Create a sample problem file"""
        sample_problems = self._generate_sample_problems(domain, 20)
        
        problem_data = {
            "domain": domain.value,
            "description": f"Sample problems for {domain.value} domain",
            "problems": [prob.to_dict() for prob in sample_problems]
        }
        
        with open(file_path, 'w') as f:
            json.dump(problem_data, f, indent=2)
    
    def save_problems(self, domain: ProblemDomain, problems: List[Problem]):
        """Save problems to file"""
        domain_file = self.data_dir / f"{domain.value}_problems.json"
        
        problem_data = {
            "domain": domain.value,
            "problems": [prob.to_dict() for prob in problems],
            "count": len(problems)
        }
        
        with open(domain_file, 'w') as f:
            json.dump(problem_data, f, indent=2)
    
    def add_custom_problem(self, problem: Problem):
        """Add a custom problem to the appropriate domain file"""
        domain_file = self.data_dir / f"{problem.domain.value}_problems.json"
        
        # Load existing problems
        if domain_file.exists():
            with open(domain_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"domain": problem.domain.value, "problems": []}
        
        # Add new problem
        data["problems"].append(problem.to_dict())
        data["count"] = len(data["problems"])
        
        # Save back
        with open(domain_file, 'w') as f:
            json.dump(data, f, indent=2)