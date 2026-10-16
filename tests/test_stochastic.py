from fractions import Fraction

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
