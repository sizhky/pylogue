"""Top-level package for Pylogue."""

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "cli",
    "health",
]

__author__ = """Yeshwanth Reddy"""
__email__ = "yyeshr@gmail.com"
__version__ = "0.1.0"

from .__pre_init__ import cli
from .health import *
