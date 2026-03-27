#!/usr/bin/env python3
"""
Command Line Interface for CoT Faithfulness Evaluator
"""

import click
import json
import asyncio
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table
from rich.progress import track

from .core.types import ProblemDomain, FaithfulnessLevel
from .evaluators.faithfulness import FaithfulnessEvaluator
from .benchmark.runner import BenchmarkRunner
from .core.config import get_config

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """CoT Faithfulness Evaluator - Systematic evaluation of reasoning authenticity in LLMs"""
    pass


@main.command()
@click.argument('problem', type=str)
@click.option('--model', '-m', default="gpt-4", help='Model to evaluate')
@click.option('--domain', '-d', type=click.Choice(['math', 'logic', 'ethics', 'code', 'science']), default='math')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def evaluate(problem: str, model: str, domain: str, output: str, verbose: bool):
    """Evaluate faithfulness of reasoning for a single problem"""
    
    console.print(f"🔍 Evaluating faithfulness for model: [bold]{model}[/bold]")
    console.print(f"📝 Problem: {problem}")
    console.print(f"🏷️  Domain: {domain}")
    
    try:
        # Initialize evaluator
        evaluator = FaithfulnessEvaluator(model_name=model)
        
        # Run evaluation
        result = asyncio.run(evaluator.evaluate_faithfulness(
            problem=problem,
            domain=ProblemDomain(domain)
        ))
        
        # Display results
        _display_result(result, verbose)
        
        # Save to file if requested
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                f.write(result.to_json())
            console.print(f"💾 Results saved to: {output}")
            
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()


@main.command()
@click.argument('problems_file', type=click.Path(exists=True))
@click.option('--model', '-m', default="gpt-4", help='Model to evaluate')
@click.option('--output-dir', '-o', type=click.Path(), default="data/results", help='Output directory')
@click.option('--parallel', '-p', type=int, default=3, help='Parallel evaluations')
def batch_evaluate(problems_file: str, model: str, output_dir: str, parallel: int):
    """Evaluate faithfulness for multiple problems from a file"""
    
    console.print(f"📋 Running batch evaluation from: {problems_file}")
    
    try:
        # Load problems
        with open(problems_file, 'r') as f:
            problems_data = json.load(f)
        
        if isinstance(problems_data, list):
            problems = problems_data
        elif isinstance(problems_data, dict) and 'problems' in problems_data:
            problems = problems_data['problems']
        else:
            raise ValueError("Invalid problems file format")
        
        console.print(f"📊 Found {len(problems)} problems to evaluate")
        
        # Initialize evaluator
        evaluator = FaithfulnessEvaluator(model_name=model)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Run evaluations
        results = []
        for i, problem_data in track(enumerate(problems), description="Evaluating..."):
            if isinstance(problem_data, str):
                problem_text = problem_data
                domain = ProblemDomain.MATH
            else:
                problem_text = problem_data.get('text', problem_data.get('problem', ''))
                domain = ProblemDomain(problem_data.get('domain', 'math'))
            
            result = asyncio.run(evaluator.evaluate_faithfulness(problem_text, domain))
            results.append(result)
            
            # Save individual result
            result_file = output_path / f"result_{i:04d}.json"
            with open(result_file, 'w') as f:
                f.write(result.to_json())
        
        # Generate summary
        _generate_batch_summary(results, output_path)
        console.print(f"✅ Batch evaluation complete. Results saved to: {output_dir}")
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()


@main.command()
@click.option('--models', '-m', default="gpt-4,claude-3", help='Comma-separated list of models')
@click.option('--domains', '-d', default="math,logic,ethics", help='Comma-separated list of domains')
@click.option('--num-problems', '-n', type=int, default=100, help='Number of problems per domain')
@click.option('--output-dir', '-o', default="data/benchmarks", help='Output directory')
def benchmark(models: str, domains: str, num_problems: int, output_dir: str):
    """Run comprehensive benchmark across multiple models and domains"""
    
    model_list = [m.strip() for m in models.split(',')]
    domain_list = [d.strip() for d in domains.split(',')]
    
    console.print("🏁 Starting comprehensive benchmark")
    console.print(f"🤖 Models: {model_list}")
    console.print(f"🏷️  Domains: {domain_list}")
    console.print(f"📊 Problems per domain: {num_problems}")
    
    try:
        # Initialize benchmark runner
        runner = BenchmarkRunner(
            models=model_list,
            domains=[ProblemDomain(d) for d in domain_list],
            num_problems=num_problems,
            output_dir=output_dir
        )
        
        # Run benchmark
        results = asyncio.run(runner.run_benchmark())
        
        console.print("✅ Benchmark complete!")
        _display_benchmark_results(results)
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()


@main.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table')
@click.option('--output', '-o', type=click.Path(), help='Save analysis to file')
def analyze(results_dir: str, format: str, output: str):
    """Analyze results from previous evaluations"""
    
    console.print(f"📊 Analyzing results from: {results_dir}")
    
    try:
        # Load all result files
        results_path = Path(results_dir)
        result_files = list(results_path.glob("result_*.json"))
        
        if not result_files:
            console.print("❌ No result files found", style="red")
            raise click.Abort()
        
        results = []
        for file_path in result_files:
            with open(file_path, 'r') as f:
                result_data = json.load(f)
                results.append(result_data)
        
        # Generate analysis
        analysis = _generate_analysis(results)
        
        if format == 'table':
            _display_analysis_table(analysis)
        elif format == 'json':
            console.print(json.dumps(analysis, indent=2))
        elif format == 'csv':
            _display_analysis_csv(analysis)
        
        if output:
            with open(output, 'w') as f:
                if format == 'json':
                    json.dump(analysis, f, indent=2)
                else:
                    f.write(str(analysis))
            console.print(f"💾 Analysis saved to: {output}")
            
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise click.Abort()


def _display_result(result, verbose: bool):
    """Display evaluation result in a formatted way"""
    
    # Main result table
    table = Table(title="Faithfulness Evaluation Result")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Model", result.model_name)
    table.add_row("Consistency Score", f"{result.consistency_score}/100")
    table.add_row("Faithfulness Level", result.faithfulness_level.value)
    table.add_row("Passed Probes", f"{result.passed_probes}/{result.total_probes}")
    
    console.print(table)
    
    if verbose:
        # Detailed probe results
        probe_table = Table(title="Probe Details")
        probe_table.add_column("Probe Type", style="cyan")
        probe_table.add_column("Result", style="green")
        probe_table.add_column("Confidence", style="yellow")
        
        for probe in result.probe_results:
            status = "✅ PASS" if probe.passed else "❌ FAIL"
            confidence = f"{probe.confidence:.2f}"
            probe_table.add_row(probe.probe_type.value, status, confidence)
        
        console.print(probe_table)
        
        # Original reasoning
        console.print("\n[bold]Original Reasoning:[/bold]")
        console.print(result.original_response)


def _generate_batch_summary(results: List, output_path: Path):
    """Generate summary statistics for batch evaluation"""
    
    summary = {
        "total_problems": len(results),
        "average_score": sum(r.consistency_score for r in results) / len(results),
        "score_distribution": {
            "high": sum(1 for r in results if r.faithfulness_level == FaithfulnessLevel.HIGH),
            "medium": sum(1 for r in results if r.faithfulness_level == FaithfulnessLevel.MEDIUM),
            "low": sum(1 for r in results if r.faithfulness_level == FaithfulnessLevel.LOW)
        },
        "probe_success_rates": {}
    }
    
    # Calculate probe success rates
    from collections import defaultdict
    probe_stats = defaultdict(list)
    
    for result in results:
        for probe in result.probe_results:
            probe_stats[probe.probe_type.value].append(probe.passed)
    
    for probe_type, passes in probe_stats.items():
        summary["probe_success_rates"][probe_type] = sum(passes) / len(passes)
    
    # Save summary
    with open(output_path / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)


def _display_benchmark_results(results):
    """Display benchmark results in a table"""
    # This would be implemented to show comparative results
    console.print("📊 Benchmark results displayed (implementation pending)")


def _generate_analysis(results):
    """Generate analysis from result data"""
    return {
        "total_evaluations": len(results),
        "average_score": sum(r.get('consistency_score', 0) for r in results) / len(results),
        "model_breakdown": {}  # Would analyze by model
    }


def _display_analysis_table(analysis):
    """Display analysis in table format"""
    console.print("📊 Analysis table (implementation pending)")


def _display_analysis_csv(analysis):
    """Display analysis in CSV format"""
    console.print("📊 Analysis CSV (implementation pending)")


if __name__ == "__main__":
    main()