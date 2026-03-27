"""
Benchmark runner for comprehensive evaluation across models and domains
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

from ..core.types import ProblemDomain, FaithfulnessResult, Problem
from ..evaluators.faithfulness import FaithfulnessEvaluator
from ..data.problems import ProblemLoader


class BenchmarkRunner:
    """Main benchmark runner for systematic evaluation"""
    
    def __init__(
        self,
        models: List[str],
        domains: List[ProblemDomain],
        num_problems: int = 100,
        output_dir: str = "data/benchmarks",
        max_parallel: int = 3
    ):
        self.models = models
        self.domains = domains
        self.num_problems = num_problems
        self.output_dir = Path(output_dir)
        self.max_parallel = max_parallel
        self.problem_loader = ProblemLoader()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized BenchmarkRunner: {len(models)} models × {len(domains)} domains × {num_problems} problems")
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark evaluation"""
        
        start_time = datetime.now()
        benchmark_id = start_time.strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Starting benchmark run: {benchmark_id}")
        
        # Load problems for all domains
        all_problems = {}
        for domain in self.domains:
            problems = self.problem_loader.load_problems(domain, self.num_problems)
            all_problems[domain] = problems
            logger.info(f"Loaded {len(problems)} problems for domain: {domain.value}")
        
        # Run evaluations for each model
        results = {}
        for model in self.models:
            logger.info(f"Starting evaluation for model: {model}")
            model_results = await self._evaluate_model(model, all_problems)
            results[model] = model_results
            
            # Save intermediate results
            self._save_model_results(benchmark_id, model, model_results)
        
        # Generate comprehensive analysis
        analysis = self._generate_benchmark_analysis(results)
        
        # Save final results
        benchmark_data = {
            "benchmark_id": benchmark_id,
            "timestamp": start_time.isoformat(),
            "config": {
                "models": self.models,
                "domains": [d.value for d in self.domains],
                "num_problems": self.num_problems
            },
            "results": results,
            "analysis": analysis,
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        
        benchmark_file = self.output_dir / f"benchmark_{benchmark_id}.json"
        with open(benchmark_file, 'w') as f:
            json.dump(benchmark_data, f, indent=2, default=str)
        
        logger.info(f"Benchmark complete. Results saved to: {benchmark_file}")
        return benchmark_data
    
    async def _evaluate_model(self, model: str, problems: Dict[ProblemDomain, List[Problem]]) -> Dict[str, Any]:
        """Evaluate a single model across all domains"""
        
        evaluator = FaithfulnessEvaluator(model_name=model)
        model_results = {}
        
        for domain, problem_list in problems.items():
            logger.info(f"Evaluating {model} on {domain.value} ({len(problem_list)} problems)")
            
            domain_results = []
            semaphore = asyncio.Semaphore(self.max_parallel)
            
            # Create evaluation tasks
            tasks = []
            for problem in problem_list:
                task = self._evaluate_with_semaphore(
                    semaphore, evaluator, problem.text, domain
                )
                tasks.append(task)
            
            # Run evaluations with concurrency control
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error evaluating problem {i}: {result}")
                    continue
                
                domain_results.append(result)
            
            model_results[domain.value] = domain_results
            logger.info(f"Completed {len(domain_results)} evaluations for {model}/{domain.value}")
        
        return model_results
    
    async def _evaluate_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore,
        evaluator: FaithfulnessEvaluator,
        problem: str,
        domain: ProblemDomain
    ) -> FaithfulnessResult:
        """Evaluate single problem with concurrency control"""
        async with semaphore:
            try:
                result = await evaluator.evaluate_faithfulness(problem, domain)
                await asyncio.sleep(0.1)  # Small delay to avoid rate limiting
                return result
            except Exception as e:
                logger.error(f"Evaluation failed for problem: {problem[:50]}... Error: {e}")
                raise
    
    def _save_model_results(self, benchmark_id: str, model: str, results: Dict[str, Any]):
        """Save intermediate results for a model"""
        model_file = self.output_dir / f"{benchmark_id}_{model.replace('/', '_')}.json"
        
        # Convert results to serializable format
        serializable_results = {}
        for domain, domain_results in results.items():
            serializable_results[domain] = [
                result.to_dict() if hasattr(result, 'to_dict') else result
                for result in domain_results
            ]
        
        with open(model_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Saved results for {model}: {model_file}")
    
    def _generate_benchmark_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis of benchmark results"""
        
        analysis = {
            "summary": {},
            "model_comparison": {},
            "domain_analysis": {},
            "probe_effectiveness": {},
            "statistical_significance": {}
        }
        
        # Summary statistics
        total_evaluations = 0
        all_scores = []
        
        for model_results in results.values():
            for domain_results in model_results.values():
                for result in domain_results:
                    total_evaluations += 1
                    if hasattr(result, 'consistency_score'):
                        all_scores.append(result.consistency_score)
        
        analysis["summary"] = {
            "total_evaluations": total_evaluations,
            "average_consistency_score": sum(all_scores) / len(all_scores) if all_scores else 0,
            "score_std": self._calculate_std(all_scores) if all_scores else 0
        }
        
        # Model comparison
        model_stats = {}
        for model, model_results in results.items():
            model_scores = []
            model_probe_stats = {}
            
            for domain_results in model_results.values():
                for result in domain_results:
                    if hasattr(result, 'consistency_score'):
                        model_scores.append(result.consistency_score)
                    
                    # Collect probe statistics
                    if hasattr(result, 'probe_results'):
                        for probe in result.probe_results:
                            probe_type = probe.probe_type.value if hasattr(probe.probe_type, 'value') else str(probe.probe_type)
                            if probe_type not in model_probe_stats:
                                model_probe_stats[probe_type] = []
                            model_probe_stats[probe_type].append(probe.passed)
            
            # Calculate probe success rates
            probe_success_rates = {}
            for probe_type, passes in model_probe_stats.items():
                probe_success_rates[probe_type] = sum(passes) / len(passes) if passes else 0
            
            model_stats[model] = {
                "average_score": sum(model_scores) / len(model_scores) if model_scores else 0,
                "score_std": self._calculate_std(model_scores) if model_scores else 0,
                "num_evaluations": len(model_scores),
                "probe_success_rates": probe_success_rates
            }
        
        analysis["model_comparison"] = model_stats
        
        # Domain analysis
        domain_stats = {}
        for domain in self.domains:
            domain_scores = []
            
            for model_results in results.values():
                domain_results = model_results.get(domain.value, [])
                for result in domain_results:
                    if hasattr(result, 'consistency_score'):
                        domain_scores.append(result.consistency_score)
            
            domain_stats[domain.value] = {
                "average_score": sum(domain_scores) / len(domain_scores) if domain_scores else 0,
                "score_std": self._calculate_std(domain_scores) if domain_scores else 0,
                "num_evaluations": len(domain_scores)
            }
        
        analysis["domain_analysis"] = domain_stats
        
        return analysis
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


class ComparisonAnalyzer:
    """Analyze and compare benchmark results"""
    
    def __init__(self, benchmark_file: str):
        with open(benchmark_file, 'r') as f:
            self.benchmark_data = json.load(f)
    
    def generate_comparison_report(self) -> str:
        """Generate a comprehensive comparison report"""
        
        report = []
        report.append("# CoT Faithfulness Evaluation Benchmark Report\n")
        
        # Summary
        analysis = self.benchmark_data.get("analysis", {})
        summary = analysis.get("summary", {})
        
        report.append(f"**Total Evaluations:** {summary.get('total_evaluations', 'N/A')}")
        report.append(f"**Average Consistency Score:** {summary.get('average_consistency_score', 0):.1f}/100")
        report.append(f"**Score Standard Deviation:** {summary.get('score_std', 0):.1f}")
        report.append("\n")
        
        # Model Rankings
        model_comparison = analysis.get("model_comparison", {})
        if model_comparison:
            report.append("## Model Performance Rankings\n")
            
            # Sort models by average score
            sorted_models = sorted(
                model_comparison.items(),
                key=lambda x: x[1].get('average_score', 0),
                reverse=True
            )
            
            for i, (model, stats) in enumerate(sorted_models, 1):
                avg_score = stats.get('average_score', 0)
                std_score = stats.get('score_std', 0)
                report.append(f"{i}. **{model}**: {avg_score:.1f} ± {std_score:.1f}")
            
            report.append("\n")
        
        # Domain Analysis
        domain_analysis = analysis.get("domain_analysis", {})
        if domain_analysis:
            report.append("## Performance by Domain\n")
            
            for domain, stats in domain_analysis.items():
                avg_score = stats.get('average_score', 0)
                report.append(f"- **{domain.title()}**: {avg_score:.1f}/100")
            
            report.append("\n")
        
        return "\n".join(report)
    
    def export_csv(self, output_path: str):
        """Export results to CSV format"""
        import csv
        
        # Flatten results for CSV
        rows = []
        results = self.benchmark_data.get("results", {})
        
        for model, model_results in results.items():
            for domain, domain_results in model_results.items():
                for i, result in enumerate(domain_results):
                    if isinstance(result, dict):
                        row = {
                            "model": model,
                            "domain": domain,
                            "problem_id": i,
                            "consistency_score": result.get("consistency_score", ""),
                            "faithfulness_level": result.get("faithfulness_level", ""),
                            "passed_probes": result.get("passed_probes", ""),
                            "total_probes": result.get("total_probes", "")
                        }
                        rows.append(row)
        
        with open(output_path, 'w', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)