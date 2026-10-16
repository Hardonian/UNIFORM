"""UNIFORM Lab: exact, scoped evidence for repeated and stochastic games."""

from .algebraic import AlgebraicField, RationalPolynomial
from .grid import periodic_grid_search
from .polytopes import PolytopeFamily, RationalPolytope
from .quitting import QuittingGame
from .rational import Q, parse_rational

__all__ = [
    "Q",
    "AlgebraicField",
    "PolytopeFamily",
    "QuittingGame",
    "RationalPolynomial",
    "RationalPolytope",
    "parse_rational",
    "periodic_grid_search",
]
__version__ = "0.2.0"
