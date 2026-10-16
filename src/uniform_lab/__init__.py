"""UNIFORM Lab: exact, scoped evidence for repeated and stochastic games."""

from .algebraic import AlgebraicField, RationalPolynomial
from .grid import periodic_grid_search
from .polytopes import PolytopeFamily, RationalPolytope
from .quitting import QuittingGame
from .rational import Q, parse_rational
from .stochastic_smt import export_discounted_stationary_qfnra

__all__ = [
    "Q",
    "AlgebraicField",
    "PolytopeFamily",
    "QuittingGame",
    "RationalPolynomial",
    "RationalPolytope",
    "export_discounted_stationary_qfnra",
    "parse_rational",
    "periodic_grid_search",
]
__version__ = "0.3.0"
