FROM python:3.10-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="CoT Faithfulness Evaluator - Systematic evaluation of reasoning authenticity"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install package in development mode
RUN pip install -e .

# Create directories
RUN mkdir -p data/results data/benchmarks logs cache

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Expose port for potential web interface
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.core.config; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "src.cli", "--help"]