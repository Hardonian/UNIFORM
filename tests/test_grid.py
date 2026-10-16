from fractions import Fraction

from uniform_lab.grid import periodic_grid_search
from uniform_lab.quitting import QuittingGame


def test_complete_grid_search_is_exact_and_reports_scope() -> None:
    game = QuittingGame(1, {1: (Fraction(1),)}, (Fraction(0),))
    result = periodic_grid_search(game, 2, 1, keep=2)
    assert result.total_profiles == 3
    assert result.evaluated_profiles == 3
    assert result.complete_global_grid
    assert result.candidates[0].maximum_regret == 0
    assert result.candidates[0].profile == ((Fraction(1, 2),),)


def test_grid_sharding_is_disjoint_by_count() -> None:
    game = QuittingGame(1, {1: (Fraction(0),)}, (Fraction(0),))
    left = periodic_grid_search(game, 4, 1, shard_index=0, shard_count=2)
    right = periodic_grid_search(game, 4, 1, shard_index=1, shard_count=2)
    assert left.evaluated_profiles + right.evaluated_profiles == 5
    assert not left.complete_global_grid
