#!/usr/bin/env python3
"""
Setup configuration for CoT Faithfulness Evaluator
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# Read requirements
def read_requirements(fname):
    with open(fname) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="cot-faithfulness-eval",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Systematic evaluation of chain-of-thought reasoning faithfulness in large language models",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/username/cot-faithfulness-eval",
    packages=find_packages(),
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0',
        ],
        'viz': [
            'matplotlib>=3.6.0',
            'seaborn>=0.12.0',
            'plotly>=5.17.0',
        ],
        'benchmark': [
            'datasets>=2.14.0',
            'huggingface-hub>=0.17.0',
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'cot-faithfulness=src.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'src': ['data/*.json', 'configs/*.yaml'],
    },
    zip_safe=False,
)