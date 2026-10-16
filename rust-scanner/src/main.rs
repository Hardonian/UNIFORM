//! Deterministic parallel screening for four-player integer-payoff quitting games.
//!
//! This is a candidate generator, not a proof engine.  It checks the one-shot pure
//! action profiles with integer arithmetic and exports full games for Python's exact
//! rational verifier.

use rayon::prelude::*;
use serde::Serialize;
use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::time::Instant;

const PLAYERS: usize = 4;
const ABSORBING_MASKS: usize = 15;

#[derive(Debug)]
struct Args {
    samples: u64,
    seed: u64,
    payoff_min: i16,
    payoff_max: i16,
    keep: usize,
    output: Option<PathBuf>,
}

#[derive(Serialize)]
struct Candidate {
    sample_id: u64,
    seed: u64,
    pure_deviation_margin: i16,
    continuation: [i16; PLAYERS],
    payoffs: Vec<[i16; PLAYERS]>,
}

#[derive(Serialize)]
struct Output {
    schema: &'static str,
    scope: &'static str,
    deterministic_rng: &'static str,
    samples: u64,
    seed: u64,
    payoff_range_inclusive: [i16; 2],
    elapsed_seconds: f64,
    samples_per_second: f64,
    matching_games: usize,
    retained_games: usize,
    candidates: Vec<Candidate>,
}

fn parse_args() -> Result<Args, String> {
    let mut result = Args {
        samples: 1_000_000,
        seed: 7,
        payoff_min: -4,
        payoff_max: 4,
        keep: 100,
        output: None,
    };
    let mut arguments = env::args().skip(1);
    while let Some(argument) = arguments.next() {
        let mut value = || {
            arguments
                .next()
                .ok_or_else(|| format!("missing value for {argument}"))
        };
        match argument.as_str() {
            "--samples" => result.samples = value()?.parse().map_err(|_| "invalid --samples")?,
            "--seed" => result.seed = value()?.parse().map_err(|_| "invalid --seed")?,
            "--min" => result.payoff_min = value()?.parse().map_err(|_| "invalid --min")?,
            "--max" => result.payoff_max = value()?.parse().map_err(|_| "invalid --max")?,
            "--keep" => result.keep = value()?.parse().map_err(|_| "invalid --keep")?,
            "--output" => result.output = Some(PathBuf::from(value()?)),
            "--help" | "-h" => {
                return Err("usage: uniform-scan [--samples N] [--seed N] [--min I] [--max I] [--keep N] [--output FILE]".into());
            }
            _ => return Err(format!("unknown argument {argument}")),
        }
    }
    if result.payoff_min > result.payoff_max {
        return Err("--min must not exceed --max".into());
    }
    Ok(result)
}

fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e3779b97f4a7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d049bb133111eb);
    value ^ (value >> 31)
}

fn payoff_value(seed: u64, sample_id: u64, index: usize, low: i16, high: i16) -> i16 {
    let key = seed
        ^ sample_id.wrapping_mul(0xd6e8feb86659fd93)
        ^ (index as u64).wrapping_mul(0xa0761d6478bd642f);
    let width = i32::from(high) - i32::from(low) + 1;
    i16::try_from(i32::from(low) + (splitmix64(key) % u64::try_from(width).unwrap()) as i32)
        .unwrap()
}

fn make_game(args: &Args, sample_id: u64) -> Vec<[i16; PLAYERS]> {
    (0..ABSORBING_MASKS)
        .map(|mask| {
            std::array::from_fn(|player| {
                payoff_value(
                    args.seed,
                    sample_id,
                    mask * PLAYERS + player,
                    args.payoff_min,
                    args.payoff_max,
                )
            })
        })
        .collect()
}

fn payoff(game: &[[i16; PLAYERS]], mask: usize, player: usize) -> i16 {
    if mask == 0 { 0 } else { game[mask - 1][player] }
}

fn no_pure_instant_equilibrium(game: &[[i16; PLAYERS]]) -> Option<i16> {
    let mut minimum_profitable_gain = i16::MAX;
    for mask in 0..=ABSORBING_MASKS {
        let mut maximum_gain = i16::MIN;
        for player in 0..PLAYERS {
            let gain = payoff(game, mask ^ (1 << player), player) - payoff(game, mask, player);
            maximum_gain = maximum_gain.max(gain);
        }
        if maximum_gain <= 0 {
            return None;
        }
        minimum_profitable_gain = minimum_profitable_gain.min(maximum_gain);
    }
    Some(minimum_profitable_gain)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = parse_args()
        .map_err(|message| std::io::Error::new(std::io::ErrorKind::InvalidInput, message))?;
    let started = Instant::now();
    let matches: Vec<(u64, i16)> = (0..args.samples)
        .into_par_iter()
        .filter_map(|sample_id| {
            let game = make_game(&args, sample_id);
            no_pure_instant_equilibrium(&game).map(|margin| (sample_id, margin))
        })
        .collect();
    let matching_games = matches.len();
    let mut ranked = matches;
    ranked.sort_unstable_by_key(|&(sample_id, margin)| (std::cmp::Reverse(margin), sample_id));
    ranked.truncate(args.keep);
    let candidates = ranked
        .into_iter()
        .map(|(sample_id, margin)| Candidate {
            sample_id,
            seed: args.seed,
            pure_deviation_margin: margin,
            continuation: [0; PLAYERS],
            payoffs: make_game(&args, sample_id),
        })
        .collect::<Vec<_>>();
    let elapsed = started.elapsed().as_secs_f64();
    let output = Output {
        schema: "uniform.rust-screen/v1",
        scope: "integer screening for absence of pure equilibria in the one-shot continuation-payoff game; not an equilibrium nonexistence claim",
        deterministic_rng: "counter-based SplitMix64 keyed by (seed,sample_id,payoff_index)",
        samples: args.samples,
        seed: args.seed,
        payoff_range_inclusive: [args.payoff_min, args.payoff_max],
        elapsed_seconds: elapsed,
        samples_per_second: args.samples as f64 / elapsed,
        matching_games,
        retained_games: candidates.len(),
        candidates,
    };
    let json = serde_json::to_string_pretty(&output)?;
    match args.output {
        Some(path) => {
            let mut writer = BufWriter::new(File::create(path)?);
            writer.write_all(json.as_bytes())?;
            writer.write_all(b"\n")?;
        }
        None => println!("{json}"),
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generator_is_deterministic() {
        let args = Args {
            samples: 1,
            seed: 7,
            payoff_min: -4,
            payoff_max: 4,
            keep: 1,
            output: None,
        };
        assert_eq!(make_game(&args, 42), make_game(&args, 42));
        assert_ne!(make_game(&args, 41), make_game(&args, 42));
    }

    #[test]
    fn constant_zero_game_has_pure_equilibria() {
        let game = vec![[0; PLAYERS]; ABSORBING_MASKS];
        assert_eq!(no_pure_instant_equilibrium(&game), None);
    }
}
