from fractions import Fraction

from uniform_lab.absorption import (
    AbsorptionPath,
    ContinuousHazard,
    DiscreteJump,
    strongly_connected_components,
    successor_graph,
)
from uniform_lab.quitting import QuittingGame


def test_continuous_and_discrete_paths_are_distinct_and_valid() -> None:
    game = QuittingGame(1, {1: (Fraction(0),)}, (Fraction(0),))
    continuous = AbsorptionPath(
        game, [ContinuousHazard(Fraction(0), Fraction(1), {1: Fraction(1)})]
    )
    jump = AbsorptionPath(game, [DiscreteJump(Fraction(0), (Fraction(1),))])
    assert continuous.check().valid
    assert jump.check().valid
    assert continuous.sequential_epsilon_check().valid
    assert jump.sequential_epsilon_check().valid


def test_continuous_path_rejects_simultaneous_quitting_density() -> None:
    payoffs = {mask: (Fraction(0), Fraction(0)) for mask in range(1, 4)}
    game = QuittingGame(2, payoffs, (Fraction(0), Fraction(0)))
    path = AbsorptionPath(game, [ContinuousHazard(Fraction(0), Fraction(1), {3: Fraction(1)})])
    assert not path.check().valid


def test_2026_successor_equation_and_sccs() -> None:
    # Example 4.4's single-quitting matrix; other absorbing outcomes are irrelevant here.
    rows = (
        (0, 2, Fraction(-1, 2), 1, 1, 1),
        (Fraction(-1, 2), 0, 2, 1, 1, 1),
        (2, Fraction(-1, 2), 0, 1, 1, 1),
        (Fraction(-3, 8), 1, 1, 0, 2, Fraction(-1, 2)),
        (1, 2, 1, Fraction(-1, 2), 0, 2),
        (2, 1, 1, 2, Fraction(-1, 2), 0),
    )
    payoffs = {mask: (Fraction(0),) * 6 for mask in range(1, 64)}
    for player, row in enumerate(rows):
        payoffs[1 << player] = tuple(map(Fraction, row))
    game = QuittingGame(6, payoffs, (Fraction(0),) * 6)
    graph = successor_graph(game)
    assert set(strongly_connected_components(graph)) == {(0, 1, 2), (3, 4, 5)}
