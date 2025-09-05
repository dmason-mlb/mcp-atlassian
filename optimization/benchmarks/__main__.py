"""Entry point for running the benchmarks package as a module.

Usage:
    python -m optimization.benchmarks.run_benchmark
"""

from .run_benchmark import main

if __name__ == "__main__":
    exit(main())