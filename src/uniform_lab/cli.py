from __future__ import annotations

import argparse
import json
import platform
import sys
from fractions import Fraction
from pathlib import Path

from .io import (
    dump_json,
    load_absorption_path,
    load_json,
    load_quitting_game,
    load_stationary_profile,
    load_stochastic_game,
)
from .quitting import (
    Profile,
    QuittingGame,
    finite_horizon_certificate,
    normalize_profile,
    periodic_regret_certificate,
)
from .rational import parse_rational, rational_text
from .screening import verify_screen_document
from .smt import export_periodic_qfnra, independently_check_model
from .solver import run_solver


def _profile(game_path: str, profile_path: str) -> tuple[QuittingGame, Profile]:
    game = load_quitting_game(game_path)
    data = load_json(profile_path)
    raw = data.get("profile") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        raise TypeError("profile file must be an array or an object with a profile array")
    return game, normalize_profile(game, raw)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uniform", description="Exact UNIFORM Lab research tools")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-game", help="strictly validate a quitting-game JSON file")
    validate.add_argument("game")

    periodic = sub.add_parser("periodic", help="certify exact bounded-period regret")
    periodic.add_argument("game")
    periodic.add_argument("profile")
    periodic.add_argument("--output")

    horizon = sub.add_parser("horizon", help="compute an exact finite-horizon certificate")
    horizon.add_argument("game")
    horizon.add_argument("profile")
    horizon.add_argument("horizon", type=int)
    horizon.add_argument("--start-phase", type=int, default=0)

    smt = sub.add_parser("smt", help="export bounded-period QF_NRA")
    smt.add_argument("game")
    smt.add_argument("--period", type=int, required=True)
    smt.add_argument("--epsilon", default="0")
    smt.add_argument("--output", required=True)

    solve = sub.add_parser("solve", help="run z3/cvc5 and stamp the result")
    solve.add_argument("smt_file")
    solve.add_argument("--solver", choices=("z3", "cvc5"), required=True)
    solve.add_argument("--timeout", type=float, default=60.0)

    check = sub.add_parser("check-model", help="independently check a rational SAT model")
    check.add_argument("game")
    check.add_argument("model")
    check.add_argument("--period", type=int, required=True)
    check.add_argument("--epsilon", default="0")

    screen = sub.add_parser("verify-screen", help="verify Rust screening output exactly")
    screen.add_argument("screen_file")

    path_check = sub.add_parser("path-check", help="check a finite symbolic absorption path")
    path_check.add_argument("game")
    path_check.add_argument("path")
    path_check.add_argument("--epsilon", default="0")

    stochastic = sub.add_parser(
        "stochastic", help="exact discounted and finite-horizon stochastic-game checks"
    )
    stochastic.add_argument("game")
    stochastic.add_argument("profile")
    stochastic.add_argument("--beta", default="9/10")
    stochastic.add_argument("--horizon", type=int, default=10)

    sub.add_parser("environment", help="print reproducibility-relevant runtime metadata")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-game":
        game = load_quitting_game(args.game)
        print(
            dump_json(
                {
                    "valid": True,
                    "players": game.players,
                    "absorbing_outcomes": len(game.payoffs),
                    "pure_instant_equilibria": list(game.pure_instant_equilibria()),
                }
            ),
            end="",
        )
        return 0
    if args.command == "periodic":
        game, profile = _profile(args.game, args.profile)
        payload = periodic_regret_certificate(game, profile).to_dict()
        text = dump_json(payload, args.output)
        if args.output is None:
            print(text, end="")
        return 0
    if args.command == "horizon":
        game, profile = _profile(args.game, args.profile)
        certificate = finite_horizon_certificate(
            game, profile, args.horizon, start_phase=args.start_phase
        )
        print(
            dump_json(
                {
                    "schema": "uniform.horizon-certificate/v1",
                    "evaluation": "absorption payoff by H; continuation payoff at boundary",
                    "horizon": certificate.horizon,
                    "start_phase": certificate.start_phase,
                    "value": [rational_text(x) for x in certificate.value],
                    "best_deviation_value": [
                        rational_text(x) for x in certificate.best_deviation_value
                    ],
                    "regret": [rational_text(x) for x in certificate.regret],
                    "maximum_regret": rational_text(certificate.maximum_regret),
                }
            ),
            end="",
        )
        return 0
    if args.command == "smt":
        game = load_quitting_game(args.game)
        epsilon = parse_rational(args.epsilon, field="epsilon")
        Path(args.output).write_text(
            export_periodic_qfnra(game, args.period, epsilon), encoding="utf-8", newline="\n"
        )
        print(args.output)
        return 0
    if args.command == "solve":
        result = run_solver(args.smt_file, args.solver, timeout=args.timeout)
        print(
            dump_json(
                {
                    "solver": result.solver,
                    "executable": result.executable,
                    "version": result.version,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            ),
            end="",
        )
        return result.returncode
    if args.command == "check-model":
        game = load_quitting_game(args.game)
        text = Path(args.model).read_text(encoding="utf-8")
        model, profile, valid = independently_check_model(
            game, args.period, parse_rational(args.epsilon, field="epsilon"), text
        )
        print(
            dump_json(
                {
                    "solver_status": model.status,
                    "independently_valid": valid,
                    "profile": [[rational_text(x) for x in phase] for phase in profile],
                    "unparsed_algebraic_values": model.algebraic_or_unknown,
                }
            ),
            end="",
        )
        return 0 if valid else 2
    if args.command == "verify-screen":
        document = load_json(args.screen_file)
        if not isinstance(document, dict):
            raise TypeError("screen file must be a JSON object")
        games = verify_screen_document(document)
        print(
            dump_json(
                {
                    "schema": "uniform.screen-verification/v1",
                    "verified_candidates": len(games),
                    "check": "absence of pure equilibrium in the one-shot continuation-payoff game",
                    "global_nonexistence_claim": False,
                }
            ),
            end="",
        )
        return 0
    if args.command == "path-check":
        game = load_quitting_game(args.game)
        path = load_absorption_path(game, args.path)
        structural = path.check()
        sequential = path.sequential_epsilon_check(parse_rational(args.epsilon, field="epsilon"))
        print(
            dump_json(
                {
                    "schema": "uniform.absorption-path-check/v1",
                    "structurally_valid": structural.valid,
                    "structural_errors": structural.errors,
                    "sequentially_epsilon_perfect": sequential.valid,
                    "sequential_violations": sequential.violations,
                    "epsilon": rational_text(sequential.epsilon),
                }
            ),
            end="",
        )
        return 0 if structural.valid and sequential.valid else 2
    if args.command == "stochastic":
        stochastic_game = load_stochastic_game(args.game)
        stationary_profile = load_stationary_profile(stochastic_game, args.profile)
        beta = parse_rational(args.beta, field="beta")
        values = stochastic_game.discounted_values(stationary_profile, beta)
        discounted_regret = stochastic_game.discounted_stationary_regret(
            stationary_profile, beta
        )
        horizon_regret = stochastic_game.finite_horizon_regret(
            stationary_profile, args.horizon
        )

        def matrix(value: tuple[tuple[Fraction, ...], ...]) -> list[list[str]]:
            return [[rational_text(entry) for entry in row] for row in value]

        print(
            dump_json(
                {
                    "schema": "uniform.stochastic-certificate/v1",
                    "beta": rational_text(beta),
                    "discounted_values": matrix(values),
                    "discounted_stationary_regret": matrix(discounted_regret),
                    "horizon": args.horizon,
                    "finite_horizon_regret": matrix(horizon_regret),
                }
            ),
            end="",
        )
        return 0
    if args.command == "environment":
        print(
            json.dumps(
                {
                    "python": sys.version,
                    "implementation": platform.python_implementation(),
                    "platform": platform.platform(),
                },
                indent=2,
            )
        )
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
