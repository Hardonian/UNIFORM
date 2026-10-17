"""UNIFORM Lab: exact, scoped evidence for repeated and stochastic games."""

from .algebraic import AlgebraicField, RationalPolynomial
from .grid import periodic_grid_search
from .polytopes import PolytopeFamily, RationalPolytope
from .quitting import QuittingGame
from .rational import Q, parse_rational
from .resources import example_names, load_example, load_schema, schema_names
from .stochastic_smt import export_discounted_stationary_qfnra

__all__ = [
    "Q",
    "AlgebraicField",
    "PolytopeFamily",
    "QuittingGame",
    "RationalPolynomial",
    "RationalPolytope",
    "export_discounted_stationary_qfnra",
    "example_names",
    "load_example",
    "load_schema",
    "parse_rational",
    "periodic_grid_search",
    "schema_names",
]
__version__ = "1.0.0rc1"
