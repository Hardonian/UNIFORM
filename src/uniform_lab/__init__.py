"""UNIFORM Lab: exact, scoped evidence for repeated and stochastic games."""

from .quitting import QuittingGame
from .rational import Q, parse_rational

__all__ = ["Q", "QuittingGame", "parse_rational"]
__version__ = "0.1.0"
