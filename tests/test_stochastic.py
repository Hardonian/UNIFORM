from fractions import Fraction
from itertools import product

from uniform_lab.stochastic import StochasticGame


def test_one_state_discounted_value_and_regret() -> None:
    game = StochasticGame(
        states=1,
        action_counts=(2,),
        payoffs={(0, (0,)): (Fraction(0),), (0, (1,)): (Fraction(2),)},
        transitions={(0, (0,)): (Fraction(1),), (0, (1,)): (Fraction(1),)},
    )
    profile = ((((Fraction(1, 2), Fraction(1, 2))),),)
    assert game.discounted_values(profile, Fraction(9, 10)) == ((Fraction(1),),)
    assert game.discounted_stationary_regret(profile, Fraction(9, 10)) == ((Fraction(1),),)
    assert game.finite_horizon_regret(profile, 5) == ((Fraction(1),),)


def test_invalid_transition_is_rejected() -> None:
    try:
        StochasticGame(
            states=1,
            action_counts=(1,),
            payoffs={(0, (0,)): (Fraction(0),)},
            transitions={(0, (0,)): (Fraction(1, 2),)},
        )
    except ValueError as exc:
        assert "sum exactly" in str(exc)
    else:
        raise AssertionError("invalid stochastic row was accepted")


def _two_state_game() -> StochasticGame:
    payoffs = {}
    transitions = {}
    for state in range(2):
        for joint in product(range(2), repeat=2):
            payoffs[state, joint] = (
                Fraction(state + 2 * joint[0] - joint[1]),
                Fraction(1 - state + joint[1] - joint[0]),
            )
            target = (state + joint[0] + joint[1]) % 2
            transitions[state, joint] = (
                Fraction(target == 0),
                Fraction(target == 1),
            )
    return StochasticGame(2, (2, 2), payoffs, transitions)


def _slow_finite_horizon_regret(
    game: StochasticGame, profile: tuple, horizon: int
) -> tuple[tuple[Fraction, ...], ...]:
    profile_total = [[Fraction(0) for _ in range(game.states)] for _ in range(game.players)]
    best_total = [[Fraction(0) for _ in range(game.states)] for _ in range(game.players)]
    for _ in range(horizon):
        next_profile = [[Fraction(0) for _ in range(game.states)] for _ in range(game.players)]
        next_best = [[Fraction(0) for _ in range(game.states)] for _ in range(game.players)]
        for player in range(game.players):
            rewards, transition = game.induced(profile, player)
            for state in range(game.states):
                next_profile[player][state] = rewards[state] + sum(
                    transition[state][target] * profile_total[player][target]
                    for target in range(game.states)
                )
                action_values = []
                for action in range(game.action_counts[player]):
                    value = Fraction(0)
                    ranges = [
                        range(game.action_counts[other]) if other != player else (action,)
                        for other in range(game.players)
                    ]
                    for joint in product(*ranges):
                        probability = Fraction(1)
                        for other, chosen in enumerate(joint):
                            if other != player:
                                probability *= profile[state][other][chosen]
                        key = (state, joint)
                        continuation = sum(
                            game.transitions[key][target] * best_total[player][target]
                            for target in range(game.states)
                        )
                        value += probability * (game.payoffs[key][player] + continuation)
                    action_values.append(value)
                next_best[player][state] = max(action_values)
        profile_total, best_total = next_profile, next_best
    return tuple(
        tuple(
            (best_total[player][state] - profile_total[player][state]) / horizon
            for player in range(game.players)
        )
        for state in range(game.states)
    )


def test_optimized_finite_horizon_matches_reference() -> None:
    game = _two_state_game()
    profile = (
        ((Fraction(1, 3), Fraction(2, 3)), (Fraction(3, 4), Fraction(1, 4))),
        ((Fraction(2, 5), Fraction(3, 5)), (Fraction(1, 2), Fraction(1, 2))),
    )
    for horizon in (1, 2, 5):
        assert game.finite_horizon_regret(profile, horizon) == _slow_finite_horizon_regret(
            game, profile, horizon
        )


def test_discounted_regret_only_solves_deviating_player(monkeypatch) -> None:
    game = _two_state_game()
    profile = (
        ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2))),
        ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2))),
    )
    calls = 0
    original = StochasticGame._discounted_player_values

    def counted(self, candidate_profile, beta, player):
        nonlocal calls
        calls += 1
        return original(self, candidate_profile, beta, player)

    monkeypatch.setattr(StochasticGame, "_discounted_player_values", counted)
    game.discounted_stationary_regret(profile, Fraction(9, 10))
    # Two base-player solves plus 2 players * 2^2 deterministic policies.
    assert calls == 10
