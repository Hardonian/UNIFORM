"""UNIFORM Lab: exact, scoped evidence for repeated and stochastic games."""

from .algebraic import AlgebraicField, RationalPolynomial
from .bivariate import (
    BivariateBox,
    BivariateExclusionCertificate,
    BivariatePolynomial,
    RationalInterval,
    branch_and_prune_2d,
    extract_bivariate_resultants,
    prune_quitting_game,
)
from .grid import periodic_grid_search
from .polytopes import PolytopeFamily, RationalPolytope
from .quitting import QuittingGame
from .rational import Q, parse_rational
from .resources import example_names, load_example, load_schema, schema_names
from .stochastic_smt import export_discounted_stationary_qfnra

__all__ = [
    "Q",
    "AlgebraicField",
    "BivariateBox",
    "BivariateExclusionCertificate",
    "BivariatePolynomial",
    "PolytopeFamily",
    "QuittingGame",
    "RationalInterval",
    "RationalPolynomial",
    "RationalPolytope",
    "branch_and_prune_2d",
    "example_names",
    "export_discounted_stationary_qfnra",
    "extract_bivariate_resultants",
    "load_example",
    "load_schema",
    "parse_rational",
    "periodic_grid_search",
    "prune_quitting_game",
    "schema_names",
]
__version__ = "1.0.0rc1"
