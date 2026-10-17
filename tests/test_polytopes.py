from fractions import Fraction

from uniform_lab.polytopes import (
    PolytopeFamily,
    RationalPolytope,
    essential_aps_polytopes,
    t_i_polytope,
)
from uniform_lab.quitting import QuittingGame


def test_exact_polytope_section_retains_full_segment_generators() -> None:
    game = QuittingGame(
        2,
        {
            1: (Fraction(0), Fraction(0)),
            2: (Fraction(0), Fraction(0)),
            3: (Fraction(0), Fraction(0)),
        },
        (Fraction(0), Fraction(0)),
    )
    continuation = RationalPolytope(((Fraction(0), Fraction(1)), (Fraction(0), Fraction(2))))
    image = t_i_polytope(game, 0, continuation)
    assert image is not None
    assert set(image.vertices) == {
        (Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(2)),
    }


def test_polytope_operator_computes_new_rational_section_endpoints() -> None:
    game = QuittingGame(
        2,
        {
            1: (Fraction(-1), Fraction(0)),
            2: (Fraction(0), Fraction(0)),
            3: (Fraction(0), Fraction(0)),
        },
        (Fraction(0), Fraction(0)),
    )
    continuation = RationalPolytope(((Fraction(1), Fraction(1)), (Fraction(1), Fraction(3))))
    image = t_i_polytope(game, 0, continuation)
    assert image is not None
    assert set(image.vertices) == {
        (Fraction(0), Fraction(1, 2)),
        (Fraction(0), Fraction(3, 2)),
    }


def test_essential_aps_includes_nonnegative_single_quit_rows() -> None:
    game = QuittingGame(1, {1: (Fraction(3),)}, (Fraction(0),))
    result = essential_aps_polytopes(game, {0: PolytopeFamily()})
    assert result[0].polytopes == (RationalPolytope(((Fraction(3),),)),)


def test_polytope_canonicalization_removes_redundant_points_and_subsets() -> None:
    segment = RationalPolytope(
        (
            (Fraction(0), Fraction(0)),
            (Fraction(1, 2), Fraction(1, 2)),
            (Fraction(1), Fraction(1)),
        )
    )
    assert segment.vertices == (
        (Fraction(0), Fraction(0)),
        (Fraction(1), Fraction(1)),
    )
    singleton = RationalPolytope(((Fraction(1, 2), Fraction(1, 2)),))
    assert PolytopeFamily((segment, singleton)).polytopes == (segment,)


def test_polytope_geometry_operations() -> None:
    # Unit square [0, 1] x [0, 1]
    square = RationalPolytope(
        (
            (Fraction(0), Fraction(0)),
            (Fraction(1), Fraction(0)),
            (Fraction(1), Fraction(1)),
            (Fraction(0), Fraction(1)),
        )
    )
    assert square.contains_point((Fraction(1, 2), Fraction(1, 2))) is True
    assert square.contains_point((Fraction(2), Fraction(2))) is False
    assert square.center_of_mass() == (Fraction(1, 2), Fraction(1, 2))

    # Support function in direction (1, 1) should be 2 at (1, 1)
    val, vert = square.support_function((Fraction(1), Fraction(1)))
    assert val == Fraction(2)
    assert vert == (Fraction(1), Fraction(1))

    # Projection onto first axis
    proj = square.project([0])
    assert set(proj.vertices) == {(Fraction(0),), (Fraction(1),)}

    # Minkowski sum with interval [0, 1] x [0, 0] gives [0, 2] x [0, 1]
    segment = RationalPolytope(((Fraction(0), Fraction(0)), (Fraction(1), Fraction(0))))
    sum_poly = square.minkowski_sum(segment)
    assert sum_poly.dimension == 2
    val_x, _ = sum_poly.support_function((Fraction(1), Fraction(0)))
    assert val_x == Fraction(2)

    # 2D H-representation
    ineqs = square.h_representation_2d()
    assert len(ineqs) == 4
