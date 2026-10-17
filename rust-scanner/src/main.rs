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
    mixed_grid: Option<usize>,
    output: Option<PathBuf>,
}

#[derive(Serialize)]
struct Candidate {
    sample_id: u64,
    seed: u64,
    pure_deviation_margin: i16,
    #[serde(skip_serializing_if = "Option::is_none")]
    min_mixed_regret: Option<f64>,
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
    #[serde(skip_serializing_if = "Option::is_none")]
    mixed_grid_steps: Option<usize>,
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
        mixed_grid: None,
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
            "--mixed-grid" => {
                result.mixed_grid = Some(value()?.parse().map_err(|_| "invalid --mixed-grid")?)
            }
            "--output" => result.output = Some(PathBuf::from(value()?)),
            "--help" | "-h" => {
                return Err("usage: uniform-scan [--samples N] [--seed N] [--min I] [--max I] [--keep N] [--mixed-grid STEPS] [--output FILE]".into());
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

fn profile_regret(game: &[[i16; PLAYERS]], q: &[f64; PLAYERS]) -> f64 {
    let mut sigma = 1.0;
    for &p in q {
        sigma *= 1.0 - p;
    }
    let abs_prob = 1.0 - sigma;

    let v: [f64; PLAYERS] = if abs_prob <= 1e-12 {
        [0.0; PLAYERS]
    } else {
        let mut r = [0.0; PLAYERS];
        for mask in 1..=ABSORBING_MASKS {
            let mut prob = 1.0;
            for (player, &q_player) in q.iter().enumerate() {
                if (mask & (1 << player)) != 0 {
                    prob *= q_player;
                } else {
                    prob *= 1.0 - q_player;
                }
            }
            if prob > 0.0 {
                for player in 0..PLAYERS {
                    r[player] += prob * (game[mask - 1][player] as f64);
                }
            }
        }
        std::array::from_fn(|p| r[p] / abs_prob)
    };

    let mut max_player_regret = 0.0f64;
    for player in 0..PLAYERS {
        let mut q_dev0 = *q;
        q_dev0[player] = 0.0;
        let mut sigma0 = 1.0;
        for &p in &q_dev0 {
            sigma0 *= 1.0 - p;
        }
        let dev0_val = if 1.0 - sigma0 <= 1e-12 {
            0.0
        } else {
            let mut r0 = 0.0;
            for mask in 1..=ABSORBING_MASKS {
                if (mask & (1 << player)) == 0 {
                    let mut prob = 1.0;
                    for (other, &q_other) in q_dev0.iter().enumerate() {
                        if (mask & (1 << other)) != 0 {
                            prob *= q_other;
                        } else {
                            prob *= 1.0 - q_other;
                        }
                    }
                    r0 += prob * (game[mask - 1][player] as f64);
                }
            }
            r0 / (1.0 - sigma0)
        };

        let mut dev1_val = 0.0;
        for mask in 1..=ABSORBING_MASKS {
            if (mask & (1 << player)) != 0 {
                let mut prob = 1.0;
                for (other, &q_other) in q.iter().enumerate() {
                    if other == player {
                        continue;
                    }
                    if (mask & (1 << other)) != 0 {
                        prob *= q_other;
                    } else {
                        prob *= 1.0 - q_other;
                    }
                }
                dev1_val += prob * (game[mask - 1][player] as f64);
            }
        }

        let best_dev = dev0_val.max(dev1_val);
        let regret = best_dev - v[player];
        if regret > max_player_regret {
            max_player_regret = regret;
        }
    }
    max_player_regret
}

fn min_mixed_grid_regret(game: &[[i16; PLAYERS]], grid_steps: usize) -> f64 {
    let mut min_regret = f64::MAX;
    let n = grid_steps.max(1);
    for i0 in 0..=n {
        let q0 = (i0 as f64) / (n as f64);
        for i1 in 0..=n {
            let q1 = (i1 as f64) / (n as f64);
            for i2 in 0..=n {
                let q2 = (i2 as f64) / (n as f64);
                for i3 in 0..=n {
                    let q3 = (i3 as f64) / (n as f64);
                    let r = profile_regret(game, &[q0, q1, q2, q3]);
                    if r < min_regret {
                        min_regret = r;
                    }
                }
            }
        }
    }
    min_regret
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = parse_args()
        .map_err(|message| std::io::Error::new(std::io::ErrorKind::InvalidInput, message))?;
    let started = Instant::now();
    let matches: Vec<(u64, i16, Option<f64>)> = (0..args.samples)
        .into_par_iter()
        .filter_map(|sample_id| {
            let game = make_game(&args, sample_id);
            no_pure_instant_equilibrium(&game).map(|margin| {
                let mixed = args
                    .mixed_grid
                    .map(|steps| min_mixed_grid_regret(&game, steps));
                (sample_id, margin, mixed)
            })
        })
        .collect();
    let matching_games = matches.len();
    let mut ranked = matches;
    if args.mixed_grid.is_some() {
        ranked.sort_unstable_by(|a, b| {
            let r_a = a.2.unwrap_or(0.0);
            let r_b = b.2.unwrap_or(0.0);
            r_b.partial_cmp(&r_a)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| std::cmp::Reverse(a.1).cmp(&std::cmp::Reverse(b.1)))
                .then_with(|| a.0.cmp(&b.0))
        });
    } else {
        ranked
            .sort_unstable_by_key(|&(sample_id, margin, _)| (std::cmp::Reverse(margin), sample_id));
    }
    ranked.truncate(args.keep);
    let candidates = ranked
        .into_iter()
        .map(|(sample_id, margin, min_mixed_regret)| Candidate {
            sample_id,
            seed: args.seed,
            pure_deviation_margin: margin,
            min_mixed_regret,
            continuation: [0; PLAYERS],
            payoffs: make_game(&args, sample_id),
        })
        .collect::<Vec<_>>();
    let elapsed = started.elapsed().as_secs_f64();
    let output = Output {
        schema: "uniform.rust-screen/v1",
        scope: "integer screening for absence of pure equilibria in the one-shot continuation-payoff game; optional mixed grid ranking",
        deterministic_rng: "counter-based SplitMix64 keyed by (seed,sample_id,payoff_index)",
        samples: args.samples,
        seed: args.seed,
        payoff_range_inclusive: [args.payoff_min, args.payoff_max],
        mixed_grid_steps: args.mixed_grid,
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
            mixed_grid: None,
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

    #[test]
    fn solan_vieille_mixed_grid_regret_is_positive() {
        let game: Vec<[i16; PLAYERS]> = vec![
            [1, 4, 0, 0],     // 1
            [4, 1, 0, 0],     // 2
            [1, 1, 1, 1],     // 3
            [0, 0, 1, 4],     // 4
            [1, 1, 1, 0],     // 5
            [0, 1, 1, 1],     // 6
            [1, 0, 0, 0],     // 7
            [0, 0, 4, 1],     // 8
            [1, 0, 1, 1],     // 9
            [1, 1, 0, 1],     // 10
            [0, 1, 0, 0],     // 11
            [1, 1, 1, 1],     // 12
            [0, 0, 0, 1],     // 13
            [0, 0, 1, 0],     // 14
            [-1, -1, -1, -1], // 15
        ];
        assert!(no_pure_instant_equilibrium(&game).is_some());
        let min_r = min_mixed_grid_regret(&game, 3);
        assert!((min_r - (1.0 / 9.0)).abs() < 1e-4);
    }
}
