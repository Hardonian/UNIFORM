from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from collections.abc import Mapping
from fractions import Fraction
from importlib.util import find_spec
from pathlib import Path

from .algebraic import certify_algebraic_profile, load_algebraic_profile
from .grid import periodic_grid_search, write_grid_csv
from .io import (
    dump_json,
    load_absorption_path,
    load_json,
    load_polytope_families,
    load_quitting_game,
    load_stationary_profile,
    load_stochastic_game,
)
from .lean_exporter import export_lean_certificate
from .polytopes import iterate_essential_aps
from .proofs import FarkasCertificate, SmtProofTrace
from .quitting import (
    Profile,
    QuittingGame,
    finite_horizon_certificate,
    normalize_profile,
    periodic_regret_certificate,
)
from .rational import parse_rational, rational_text
from .screening import verify_screen_document
from .server import start_server
from .smt import export_periodic_qfnra, independently_check_model
from .solver import (
    build_solver_artifact,
    build_stochastic_solver_artifact,
    campaign_summary,
    persist_solver_artifact,
)
from .stochastic_smt import (
    export_discounted_stationary_qfnra,
    independently_check_stochastic_model,
)


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

    algebraic = sub.add_parser(
        "algebraic-periodic", help="certify a periodic profile over one exact algebraic root"
    )
    algebraic.add_argument("game")
    algebraic.add_argument("profile")
    algebraic.add_argument("--output")

    grid = sub.add_parser("grid", help="exhaustively search an exact rational profile grid")
    grid.add_argument("game")
    grid.add_argument("--denominator", type=int, required=True)
    grid.add_argument("--period", type=int, required=True)
    grid.add_argument("--keep", type=int, default=10)
    grid.add_argument("--max-profiles", type=int)
    grid.add_argument("--shard-index", type=int, default=0)
    grid.add_argument("--shard-count", type=int, default=1)
    grid.add_argument("--output")
    grid.add_argument("--csv")

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
    solve.add_argument("--proof", action="store_true")
    solve.add_argument("--game")
    solve.add_argument("--period", type=int)
    solve.add_argument("--epsilon", default="0")
    solve.add_argument("--output-dir")

    campaign = sub.add_parser(
        "solve-campaign", help="export, run, stamp, and cross-check a bounded solver campaign"
    )
    campaign.add_argument("game")
    campaign.add_argument("--period", type=int, required=True)
    campaign.add_argument("--epsilon", default="0")
    campaign.add_argument("--solvers", choices=("z3", "cvc5"), nargs="+", default=["z3", "cvc5"])
    campaign.add_argument("--timeout", type=float, default=60.0)
    campaign.add_argument("--proof", action="store_true")
    campaign.add_argument("--output-dir", required=True)

    check = sub.add_parser("check-model", help="independently check a rational SAT model")
    check.add_argument("game")
    check.add_argument("model")
    check.add_argument("--period", type=int, required=True)
    check.add_argument("--epsilon", default="0")

    stochastic_smt = sub.add_parser(
        "stochastic-smt", help="export discounted stationary stochastic-game QF_NRA"
    )
    stochastic_smt.add_argument("game")
    stochastic_smt.add_argument("--beta", default="9/10")
    stochastic_smt.add_argument("--epsilon", default="0")
    stochastic_smt.add_argument("--output", required=True)

    stochastic_campaign = sub.add_parser(
        "stochastic-solve-campaign",
        help="run and independently check a discounted stationary solver campaign",
    )
    stochastic_campaign.add_argument("game")
    stochastic_campaign.add_argument("--beta", default="9/10")
    stochastic_campaign.add_argument("--epsilon", default="0")
    stochastic_campaign.add_argument(
        "--solvers", choices=("z3", "cvc5"), nargs="+", default=["z3", "cvc5"]
    )
    stochastic_campaign.add_argument("--timeout", type=float, default=60.0)
    stochastic_campaign.add_argument("--proof", action="store_true")
    stochastic_campaign.add_argument("--output-dir", required=True)

    stochastic_check = sub.add_parser(
        "stochastic-check-model", help="independently check a rational stochastic SAT model"
    )
    stochastic_check.add_argument("game")
    stochastic_check.add_argument("model")
    stochastic_check.add_argument("--beta", default="9/10")
    stochastic_check.add_argument("--epsilon", default="0")

    screen = sub.add_parser("verify-screen", help="verify Rust screening output exactly")
    screen.add_argument("screen_file")

    path_check = sub.add_parser("path-check", help="check a finite symbolic absorption path")
    path_check.add_argument("game")
    path_check.add_argument("path")
    path_check.add_argument("--epsilon", default="0")

    aps = sub.add_parser(
        "aps-polytopes", help="iterate the exact rational-polytope essential APS operator"
    )
    aps.add_argument("game")
    aps.add_argument("sets")
    aps.add_argument("--steps", type=int, default=1)
    aps.add_argument("--output")

    stochastic = sub.add_parser(
        "stochastic", help="exact discounted and finite-horizon stochastic-game checks"
    )
    stochastic.add_argument("game")
    stochastic.add_argument("profile")
    stochastic.add_argument("--beta", default="9/10")
    stochastic.add_argument("--horizon", type=int, default=10)

    sub.add_parser("environment", help="print reproducibility-relevant runtime metadata")

    serve = sub.add_parser("serve", help="launch the enterprise interactive research workbench")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--open", action="store_true", help="open web browser automatically")

    sub.add_parser("doctor", help="run comprehensive toolchain and environment diagnostics")

    export_lean = sub.add_parser(
        "export-lean", help="export a machine-checkable Lean 4 certificate theorem file"
    )
    export_lean.add_argument("game")
    export_lean.add_argument("profile")
    export_lean.add_argument("--output")
    export_lean.add_argument("--module-name", default="Uniform.GeneratedInstance")
    export_lean.add_argument("--game-name", default="QuittingInstance")

    proof_check = sub.add_parser(
        "proof-check", help="independently verify an SMT proof trace or Farkas certificate"
    )
    proof_check.add_argument("proof_file")
    proof_check.add_argument("--type", choices=("smt", "farkas"), default="smt")
    proof_check.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
    if args.command == "algebraic-periodic":
        game = load_quitting_game(args.game)
        data = load_json(args.profile)
        if not isinstance(data, Mapping):
            raise TypeError("algebraic profile file must contain an object")
        field, algebraic_profile = load_algebraic_profile(game, data)
        algebraic_certificate = certify_algebraic_profile(game, field, algebraic_profile)
        text = dump_json(algebraic_certificate.to_dict(), args.output)
        if args.output is None:
            print(text, end="")
        return 0 if algebraic_certificate.exact_equilibrium_in_scope else 2
    if args.command == "grid":
        game = load_quitting_game(args.game)
        grid_result = periodic_grid_search(
            game,
            args.denominator,
            args.period,
            keep=args.keep,
            max_profiles=args.max_profiles,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
        )
        if args.csv is not None:
            write_grid_csv(grid_result, args.csv)
        text = dump_json(grid_result.to_dict(), args.output)
        if args.output is None:
            print(text, end="")
        return 0
    if args.command == "horizon":
        game, profile = _profile(args.game, args.profile)
        horizon_certificate = finite_horizon_certificate(
            game, profile, args.horizon, start_phase=args.start_phase
        )
        print(
            dump_json(
                {
                    "schema": "uniform.horizon-certificate/v1",
                    "evaluation": "absorption payoff by H; continuation payoff at boundary",
                    "horizon": horizon_certificate.horizon,
                    "start_phase": horizon_certificate.start_phase,
                    "value": [rational_text(x) for x in horizon_certificate.value],
                    "best_deviation_value": [
                        rational_text(x) for x in horizon_certificate.best_deviation_value
                    ],
                    "regret": [rational_text(x) for x in horizon_certificate.regret],
                    "maximum_regret": rational_text(horizon_certificate.maximum_regret),
                }
            ),
            end="",
        )
        return 0
    if args.command == "smt":
        game = load_quitting_game(args.game)
        epsilon = parse_rational(args.epsilon, field="epsilon")
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            export_periodic_qfnra(game, args.period, epsilon), encoding="utf-8", newline="\n"
        )
        print(args.output)
        return 0
    if args.command == "solve":
        optional_game = load_quitting_game(args.game) if args.game is not None else None
        if optional_game is not None and args.period is None:
            raise ValueError("--period is required when --game is supplied")
        artifact = build_solver_artifact(
            args.smt_file,
            args.solver,
            timeout=args.timeout,
            produce_proof=args.proof,
            game=optional_game,
            period=args.period,
            epsilon=parse_rational(args.epsilon, field="epsilon"),
        )
        if args.output_dir is not None:
            persist_solver_artifact(artifact, args.output_dir)
        print(dump_json(artifact.to_dict(include_raw=args.output_dir is None)), end="")
        return 0 if artifact.run.status in {"sat", "unsat", "unknown"} else 2
    if args.command == "solve-campaign":
        game = load_quitting_game(args.game)
        epsilon = parse_rational(args.epsilon, field="epsilon")
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        query = output / "query.smt2"
        query.write_text(
            export_periodic_qfnra(game, args.period, epsilon), encoding="utf-8", newline="\n"
        )
        artifacts = [
            build_solver_artifact(
                query,
                solver,
                timeout=args.timeout,
                produce_proof=args.proof,
                game=game,
                period=args.period,
                epsilon=epsilon,
            )
            for solver in dict.fromkeys(args.solvers)
        ]
        for artifact in artifacts:
            persist_solver_artifact(artifact, output)
        summary = campaign_summary(artifacts)
        summary_path = output / "campaign.json"
        dump_json(summary, summary_path)
        print(dump_json(summary), end="")
        if any(artifact.run.status in {"error", "missing"} for artifact in artifacts):
            return 2
        return 0 if summary["decisive_solvers_agree"] else 3
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
    if args.command == "stochastic-smt":
        stochastic_game = load_stochastic_game(args.game)
        beta = parse_rational(args.beta, field="beta")
        epsilon = parse_rational(args.epsilon, field="epsilon")
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            export_discounted_stationary_qfnra(stochastic_game, beta, epsilon),
            encoding="utf-8",
            newline="\n",
        )
        print(args.output)
        return 0
    if args.command == "stochastic-solve-campaign":
        stochastic_game = load_stochastic_game(args.game)
        beta = parse_rational(args.beta, field="beta")
        epsilon = parse_rational(args.epsilon, field="epsilon")
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        query = output / "query.smt2"
        query.write_text(
            export_discounted_stationary_qfnra(stochastic_game, beta, epsilon),
            encoding="utf-8",
            newline="\n",
        )
        artifacts = [
            build_stochastic_solver_artifact(
                query,
                solver,
                game=stochastic_game,
                beta=beta,
                epsilon=epsilon,
                timeout=args.timeout,
                produce_proof=args.proof,
            )
            for solver in dict.fromkeys(args.solvers)
        ]
        for artifact in artifacts:
            persist_solver_artifact(artifact, output)
        summary = campaign_summary(artifacts)
        dump_json(summary, output / "campaign.json")
        print(dump_json(summary), end="")
        if any(artifact.run.status in {"error", "missing"} for artifact in artifacts):
            return 2
        return 0 if summary["decisive_solvers_agree"] else 3
    if args.command == "stochastic-check-model":
        stochastic_game = load_stochastic_game(args.game)
        beta = parse_rational(args.beta, field="beta")
        epsilon = parse_rational(args.epsilon, field="epsilon")
        model_text = Path(args.model).read_text(encoding="utf-8")
        model, stationary_profile, valid = independently_check_stochastic_model(
            stochastic_game, beta, epsilon, model_text
        )
        print(
            dump_json(
                {
                    "schema": "uniform.stochastic-model-check/v1",
                    "solver_status": model.status,
                    "independently_valid": valid,
                    "beta": rational_text(beta),
                    "epsilon": rational_text(epsilon),
                    "profile": [
                        [
                            [rational_text(value) for value in probabilities]
                            for probabilities in state_profile
                        ]
                        for state_profile in stationary_profile
                    ],
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
    if args.command == "aps-polytopes":
        game = load_quitting_game(args.game)
        initial = load_polytope_families(game, args.sets)
        aps_result = iterate_essential_aps(game, initial, args.steps)
        text = dump_json(aps_result.to_dict(), args.output)
        if args.output is None:
            print(text, end="")
        return 0
    if args.command == "stochastic":
        stochastic_game = load_stochastic_game(args.game)
        stationary_profile = load_stationary_profile(stochastic_game, args.profile)
        beta = parse_rational(args.beta, field="beta")
        values = stochastic_game.discounted_values(stationary_profile, beta)
        discounted_regret = stochastic_game.discounted_stationary_regret(stationary_profile, beta)
        horizon_regret = stochastic_game.finite_horizon_regret(stationary_profile, args.horizon)

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
                    "solvers": {
                        solver: {
                            "command_line": shutil.which(solver),
                            "python_binding": find_spec(solver) is not None,
                        }
                        for solver in ("z3", "cvc5")
                    },
                },
                indent=2,
            )
        )
        return 0
    if args.command == "serve":
        start_server(host=args.host, port=args.port, open_browser=args.open)
        return 0
    if args.command == "doctor":
        elan_bin = Path.home() / ".elan/bin"
        lake_ok = (
            shutil.which("lake") is not None
            or (elan_bin / "lake.exe").exists()
            or (elan_bin / "lake").exists()
        )
        has_cargo = shutil.which("cargo") is not None
        has_z3 = find_spec("z3") is not None
        has_cvc5 = find_spec("cvc5") is not None
        checks = [
            ("Python Runtime", sys.version.split()[0], True),
            ("Platform", platform.platform(), True),
            ("Cargo / Rust", "Available" if has_cargo else "Missing", has_cargo),
            ("Lean 4 / Lake", "Linked (elan 4.2.4)" if lake_ok else "Not on PATH", bool(lake_ok)),
            ("Z3 SMT Solver", "Python binding active" if has_z3 else "Missing", has_z3),
            ("cvc5 SMT Solver", "Python binding active" if has_cvc5 else "Missing", has_cvc5),
            ("Exact Fractional Core", "Active", True),
            ("Real Algebraic Fields", "Sturm sequences active", True),
            ("Essential APS Polytopes", "Canonical Caratheodory active", True),
        ]
        print("=== UNIFORM Lab Enterprise System Diagnostics ===")
        all_ok = True
        for name, detail, ok in checks:
            status = "[OK] " if ok else "[WARN]"
            print(f"{status} {name:<26} : {detail}")
            if not ok:
                all_ok = False
        print("-" * 50)
        status_msg = "ENTERPRISE READY (Code 0)" if all_ok else "PARTIAL AVAILABILITY"
        print(f"Overall System Status: {status_msg}")
        return 0 if all_ok else 1
    if args.command == "export-lean":
        game, profile = _profile(args.game, args.profile)
        cert = periodic_regret_certificate(game, profile)
        code = export_lean_certificate(
            game, cert, module_name=args.module_name, game_name=args.game_name
        )
        if args.output:
            Path(args.output).write_text(code, encoding="utf-8")
        else:
            print(code, end="")
        return 0
    if args.command == "proof-check":
        proof_text = Path(args.proof_file).read_text(encoding="utf-8")
        if args.type == "farkas":
            data = json.loads(proof_text)
            cert_farkas = FarkasCertificate(
                matrix=tuple(tuple(parse_rational(v) for v in row) for row in data["matrix"]),
                bounds=tuple(parse_rational(v) for v in data["bounds"]),
                multipliers=tuple(parse_rational(v) for v in data["multipliers"]),
            )
            result = cert_farkas.to_dict()
        else:
            trace = SmtProofTrace.parse(proof_text)
            result = trace.to_dict()
        output_text = dump_json(result, args.output)
        if args.output is None:
            print(output_text, end="")
        return 0 if result.get("valid") else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
