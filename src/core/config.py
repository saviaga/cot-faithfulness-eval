"""
Configuration management for CoT Faithfulness Evaluator
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from .types import EvaluationConfig, BenchmarkConfig, ProblemDomain, ProbeType

# Load environment variables
load_dotenv()


class Config:
    """Main configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self._config_data = self._load_config()
    
    def _find_config_path(self) -> str:
        """Find configuration file"""
        possible_paths = [
            os.environ.get("COT_CONFIG_PATH"),
            "config.yaml",
            "configs/default.yaml",
            os.path.expanduser("~/.cot-faithfulness/config.yaml"),
        ]
        
        for path in possible_paths:
            if path and Path(path).exists():
                return path
        
        # Return default path if none found
        return "configs/default.yaml"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "models": {
                "default": "gpt-4",
                "providers": {
                    "openai": {
                        "api_key": os.environ.get("OPENAI_API_KEY"),
                        "base_url": "https://api.openai.com/v1",
                        "models": ["gpt-4", "gpt-3.5-turbo"]
                    },
                    "anthropic": {
                        "api_key": os.environ.get("ANTHROPIC_API_KEY"),
                        "base_url": "https://api.anthropic.com",
                        "models": ["claude-3-opus", "claude-3-sonnet"]
                    }
                }
            },
            "evaluation": {
                "temperature": 0.1,
                "max_tokens": 800,
                "timeout": 30,
                "rate_limit_delay": 1.0,
                "retry_attempts": 3
            },
            "probes": {
                "enabled": ["corruption", "alternative_method", "dependency", "counterfactual"],
                "thresholds": {
                    "high_faithfulness": 75,
                    "medium_faithfulness": 50
                }
            },
            "benchmark": {
                "default_domains": ["math", "logic", "ethics"],
                "problems_per_domain": 100,
                "parallel_requests": 5
            },
            "output": {
                "results_dir": "data/results",
                "save_intermediate": True,
                "export_formats": ["json", "csv"]
            },
            "logging": {
                "level": "INFO",
                "file": "logs/faithfulness.log"
            }
        }
    
    def get_evaluation_config(self, model_name: str) -> EvaluationConfig:
        """Get evaluation configuration for a model"""
        model_config = self._get_model_config(model_name)
        eval_config = self._config_data.get("evaluation", {})
        probe_config = self._config_data.get("probes", {})
        
        return EvaluationConfig(
            model_name=model_name,
            api_key=model_config["api_key"],
            base_url=model_config.get("base_url"),
            temperature=eval_config.get("temperature", 0.1),
            max_tokens=eval_config.get("max_tokens", 800),
            timeout=eval_config.get("timeout", 30),
            rate_limit_delay=eval_config.get("rate_limit_delay", 1.0),
            retry_attempts=eval_config.get("retry_attempts", 3),
            probe_types=[ProbeType(p) for p in probe_config.get("enabled", [])]
        )
    
    def get_benchmark_config(self) -> BenchmarkConfig:
        """Get benchmark configuration"""
        benchmark_config = self._config_data.get("benchmark", {})
        
        return BenchmarkConfig(
            models=self._get_available_models(),
            domains=[ProblemDomain(d) for d in benchmark_config.get("default_domains", ["math"])],
            num_problems=benchmark_config.get("problems_per_domain", 100),
            output_dir=self._config_data.get("output", {}).get("results_dir", "data/results"),
            parallel_requests=benchmark_config.get("parallel_requests", 5)
        )
    
    def _get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific model"""
        providers = self._config_data.get("models", {}).get("providers", {})
        
        for provider, config in providers.items():
            if model_name in config.get("models", []):
                return {
                    "api_key": config.get("api_key") or os.environ.get(f"{provider.upper()}_API_KEY"),
                    "base_url": config.get("base_url"),
                    "provider": provider
                }
        
        # Default to OpenAI if not found
        return {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/v1",
            "provider": "openai"
        }
    
    def _get_available_models(self) -> list[str]:
        """Get list of available models"""
        models = []
        providers = self._config_data.get("models", {}).get("providers", {})
        
        for provider_config in providers.values():
            models.extend(provider_config.get("models", []))
        
        return models
    
    def get_faithfulness_thresholds(self) -> Dict[str, int]:
        """Get faithfulness level thresholds"""
        probe_config = self._config_data.get("probes", {})
        return probe_config.get("thresholds", {
            "high_faithfulness": 75,
            "medium_faithfulness": 50
        })
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self._config_data.get("output", {
            "results_dir": "data/results",
            "save_intermediate": True,
            "export_formats": ["json", "csv"]
        })
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        path = config_path or self.config_path
        
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.dump(self._config_data, f, default_flow_style=False, indent=2)


# Global config instance
config = Config()


def get_config() -> Config:
    """Get global configuration instance"""
    return config


def reload_config(config_path: Optional[str] = None):
    """Reload configuration from file"""
    global config
    config = Config(config_path)