//! Deterministic parallel screening for four-player integer-payoff quitting games.
//!
//! Features:
//! 1. Candidate generator: checks one-shot pure action profiles and exports games for Python.
//! 2. Arbitrary-period cyclic screening (--audit-game): Rayon multi-core exhaustive grid evaluation
//!    for arbitrary periods P and denominators D, verifying periodic regret bounds.

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs::File;
use std::io::{BufReader, BufWriter, Write};
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
    audit_game: Option<PathBuf>,
    period: usize,
    denominator: usize,
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

#[derive(Deserialize)]
struct QuittingGameJson {
    players: usize,
    #[serde(default)]
    continuation: Vec<f64>,
    payoffs: BTreeMap<String, Vec<f64>>,
    #[serde(default)]
    title: String,
}

#[derive(Serialize)]
struct PeriodicCandidateOutput {
    profile: Vec<Vec<String>>,
    maximum_regret: String,
    maximum_regret_float: f64,
}

#[derive(Serialize)]
struct PeriodicAuditOutput {
    schema: &'static str,
    scope: &'static str,
    game_path: String,
    game_title: String,
    denominator: usize,
    period: usize,
    players: usize,
    total_profiles: u64,
    evaluated_profiles: u64,
    complete_shard: bool,
    complete_global_grid: bool,
    elapsed_seconds: f64,
    profiles_per_second: f64,
    min_regret_floor: f64,
    best: Vec<PeriodicCandidateOutput>,
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
        audit_game: None,
        period: 1,
        denominator: 2,
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
            "--audit-game" => result.audit_game = Some(PathBuf::from(value()?)),
            "--period" => result.period = value()?.parse().map_err(|_| "invalid --period")?,
            "--denominator" => {
                result.denominator = value()?.parse().map_err(|_| "invalid --denominator")?
            }
            "--help" | "-h" => {
                return Err("usage: uniform-scan [--samples N] [--seed N] [--min I] [--max I] [--keep N] [--mixed-grid STEPS] [--output FILE] [--audit-game FILE] [--period P] [--denominator D]".into());
            }
            _ => return Err(format!("unknown argument {argument}")),
        }
    }
    if result.payoff_min > result.payoff_max {
        return Err("--min must not exceed --max".into());
    }
    if result.period == 0 {
        return Err("--period must be at least 1".into());
    }
    if result.denominator == 0 {
        return Err("--denominator must be at least 1".into());
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

// ---------------------------------------------------------------------------
// High-Period Multi-Phase Cyclic Grid Screening Engine (P >= 1)
// ---------------------------------------------------------------------------

fn parse_mask(key: &str, players: usize) -> Result<usize, String> {
    if let Some(stripped) = key.strip_prefix("0b") {
        usize::from_str_radix(stripped, 2).map_err(|e| e.to_string())
    } else if key.len() == players && key.chars().all(|c| c == '0' || c == '1') {
        let mut mask = 0;
        for (i, c) in key.chars().enumerate() {
            if c == '1' {
                mask |= 1 << i;
            }
        }
        Ok(mask)
    } else {
        key.parse::<usize>().map_err(|e| e.to_string())
    }
}

fn format_rational(val: f64, denom: usize) -> String {
    let num = (val * (denom as f64)).round() as i64;
    let d = denom as i64;
    fn gcd(mut a: i64, mut b: i64) -> i64 {
        while b != 0 {
            let t = b;
            b = a % b;
            a = t;
        }
        a.abs()
    }
    let g = gcd(num, d);
    let simp_num = num / g;
    let simp_d = d / g;
    if simp_d == 1 {
        format!("{simp_num}")
    } else {
        format!("{simp_num}/{simp_d}")
    }
}

fn decode_profile(mut k: u64, period: usize, values: &[f64]) -> Vec<[f64; PLAYERS]> {
    let m = values.len() as u64;
    let total_coords = period * PLAYERS;
    let mut flat = vec![0.0; total_coords];
    for coord in (0..total_coords).rev() {
        let digit = (k % m) as usize;
        k /= m;
        flat[coord] = values[digit];
    }
    let mut profile = Vec::with_capacity(period);
    for t in 0..period {
        let mut phase = [0.0; PLAYERS];
        for p in 0..PLAYERS {
            phase[p] = flat[t * PLAYERS + p];
        }
        profile.push(phase);
    }
    profile
}

fn periodic_profile_regret(
    game_payoffs: &[[f64; PLAYERS]; 16],
    continuation: &[f64; PLAYERS],
    period: usize,
    profile: &[[f64; PLAYERS]],
) -> f64 {
    // 1. Stage terms for baseline profile
    let mut survival = Vec::with_capacity(period);
    let mut rewards = Vec::with_capacity(period);
    for t in 0..period {
        let q = &profile[t];
        let mut surv = 1.0;
        for &p in q {
            surv *= 1.0 - p;
        }
        survival.push(surv);

        let mut rew = [0.0; PLAYERS];
        for mask in 1..=15 {
            let mut prob = 1.0;
            for player in 0..PLAYERS {
                if (mask & (1 << player)) != 0 {
                    prob *= q[player];
                } else {
                    prob *= 1.0 - q[player];
                }
            }
            if prob > 0.0 {
                for player in 0..PLAYERS {
                    rew[player] += prob * game_payoffs[mask][player];
                }
            }
        }
        rewards.push(rew);
    }

    // 2. Baseline cycle values
    let mut cycle_survival = 1.0;
    for &s in &survival {
        cycle_survival *= s;
    }

    let mut values = vec![[0.0; PLAYERS]; period];
    if (1.0 - cycle_survival).abs() <= 1e-14 {
        for start in 0..period {
            values[start] = *continuation;
        }
    } else {
        let denom = 1.0 - cycle_survival;
        for start in 0..period {
            let mut prefix = 1.0;
            let mut num = [0.0; PLAYERS];
            for offset in 0..period {
                let phase = (start + offset) % period;
                for player in 0..PLAYERS {
                    num[player] += prefix * rewards[phase][player];
                }
                prefix *= survival[phase];
            }
            for player in 0..PLAYERS {
                values[start][player] = num[player] / denom;
            }
        }
    }

    // 3. Precompute opponent branch terms for each player and phase
    let mut surv_0 = vec![[1.0; PLAYERS]; period];
    let mut rew_0 = vec![[0.0; PLAYERS]; period];
    let mut rew_1 = vec![[0.0; PLAYERS]; period];

    for t in 0..period {
        let q = &profile[t];
        for player in 0..PLAYERS {
            let mut s0 = 1.0;
            for other in 0..PLAYERS {
                if other != player {
                    s0 *= 1.0 - q[other];
                }
            }
            surv_0[t][player] = s0;

            let mut r0 = 0.0;
            for mask in 1..=15 {
                if (mask & (1 << player)) == 0 {
                    let mut prob = 1.0;
                    for other in 0..PLAYERS {
                        if other != player {
                            if (mask & (1 << other)) != 0 {
                                prob *= q[other];
                            } else {
                                prob *= 1.0 - q[other];
                            }
                        }
                    }
                    if prob > 0.0 {
                        r0 += prob * game_payoffs[mask][player];
                    }
                }
            }
            rew_0[t][player] = r0;

            let mut r1 = 0.0;
            for mask in 1..=15 {
                if (mask & (1 << player)) != 0 {
                    let mut prob = 1.0;
                    for other in 0..PLAYERS {
                        if other != player {
                            if (mask & (1 << other)) != 0 {
                                prob *= q[other];
                            } else {
                                prob *= 1.0 - q[other];
                            }
                        }
                    }
                    if prob > 0.0 {
                        r1 += prob * game_payoffs[mask][player];
                    }
                }
            }
            rew_1[t][player] = r1;
        }
    }

    // 4. Deviation search across all 2^period pure policies for each player
    let num_policies = 1 << period;
    let mut max_profile_regret = 0.0f64;

    for player in 0..PLAYERS {
        let mut best_dev_values = vec![f64::NEG_INFINITY; period];

        for policy_mask in 0..num_policies {
            let mut dev_cycle_s = 1.0;
            let mut s_arr = [0.0; 8];
            let mut r_arr = [0.0; 8];

            for t in 0..period {
                let action = (policy_mask >> t) & 1;
                if action == 1 {
                    s_arr[t] = 0.0;
                    r_arr[t] = rew_1[t][player];
                    dev_cycle_s = 0.0;
                } else {
                    let st = surv_0[t][player];
                    s_arr[t] = st;
                    r_arr[t] = rew_0[t][player];
                    dev_cycle_s *= st;
                }
            }

            if (1.0 - dev_cycle_s).abs() <= 1e-14 {
                let c = continuation[player];
                for start in 0..period {
                    if c > best_dev_values[start] {
                        best_dev_values[start] = c;
                    }
                }
            } else {
                let denom = 1.0 - dev_cycle_s;
                for start in 0..period {
                    let mut prefix = 1.0;
                    let mut num = 0.0;
                    for offset in 0..period {
                        let phase = (start + offset) % period;
                        num += prefix * r_arr[phase];
                        prefix *= s_arr[phase];
                    }
                    let val = num / denom;
                    if val > best_dev_values[start] {
                        best_dev_values[start] = val;
                    }
                }
            }
        }

        for start in 0..period {
            let reg = best_dev_values[start] - values[start][player];
            if reg > max_profile_regret {
                max_profile_regret = reg;
            }
        }
    }

    max_profile_regret
}

struct ThreadState {
    min_regret: f64,
    best_candidates: Vec<(f64, u64)>,
}

fn run_audit_game(args: &Args, path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let game_json: QuittingGameJson = serde_json::from_reader(reader)?;

    let mut payoffs_arr = [[0.0; PLAYERS]; 16];
    for (k, vec) in &game_json.payoffs {
        let mask = parse_mask(k, game_json.players)
            .map_err(|e| format!("invalid payoff mask {k}: {e}"))?;
        if (1..=15).contains(&mask) {
            for p in 0..PLAYERS {
                payoffs_arr[mask][p] = vec[p];
            }
        }
    }
    let mut continuation_arr = [0.0; PLAYERS];
    for p in 0..PLAYERS.min(game_json.continuation.len()) {
        continuation_arr[p] = game_json.continuation[p];
    }

    let p = args.period;
    let d = args.denominator;
    let values: Vec<f64> = (0..=d).map(|k| (k as f64) / (d as f64)).collect();
    let m = values.len() as u64;
    let total_coords = (p * PLAYERS) as u32;
    let total_profiles = m.pow(total_coords);
    let keep = args.keep;

    eprintln!(
        "UNIFORM Rust Scanner: Auditing '{}' for Period P={}, Denominator D={} ({} profiles)...",
        path.display(),
        p,
        d,
        total_profiles
    );

    let started = Instant::now();

    let state = (0..total_profiles)
        .into_par_iter()
        .fold(
            || ThreadState {
                min_regret: f64::MAX,
                best_candidates: Vec::new(),
            },
            |mut state, idx| {
                let prof = decode_profile(idx, p, &values);
                let r = periodic_profile_regret(&payoffs_arr, &continuation_arr, p, &prof);
                if r < state.min_regret {
                    state.min_regret = r;
                }
                let threshold = state
                    .best_candidates
                    .last()
                    .map(|c| c.0)
                    .unwrap_or(f64::MAX);
                if r <= threshold || state.best_candidates.len() < keep {
                    state.best_candidates.push((r, idx));
                    state.best_candidates.sort_by(|a, b| {
                        a.0.partial_cmp(&b.0)
                            .unwrap_or(std::cmp::Ordering::Equal)
                            .then_with(|| a.1.cmp(&b.1))
                    });
                    if state.best_candidates.len() > keep {
                        state.best_candidates.truncate(keep);
                    }
                }
                state
            },
        )
        .reduce(
            || ThreadState {
                min_regret: f64::MAX,
                best_candidates: Vec::new(),
            },
            |mut a, mut b| {
                let min_r = a.min_regret.min(b.min_regret);
                a.best_candidates.append(&mut b.best_candidates);
                a.best_candidates.sort_by(|x, y| {
                    x.0.partial_cmp(&y.0)
                        .unwrap_or(std::cmp::Ordering::Equal)
                        .then_with(|| x.1.cmp(&y.1))
                });
                a.best_candidates.dedup_by_key(|x| x.1);
                if a.best_candidates.len() > keep {
                    a.best_candidates.truncate(keep);
                }
                ThreadState {
                    min_regret: min_r,
                    best_candidates: a.best_candidates,
                }
            },
        );

    let elapsed = started.elapsed().as_secs_f64();
    let speed = (total_profiles as f64) / elapsed;

    eprintln!(
        "Screening complete in {:.3}s ({:.1} profiles/s). Min regret floor: {:.6}",
        elapsed, speed, state.min_regret
    );

    let best_candidates = state
        .best_candidates
        .into_iter()
        .map(|(reg, idx)| {
            let prof = decode_profile(idx, p, &values);
            let formatted_prof = prof
                .into_iter()
                .map(|phase| {
                    phase
                        .into_iter()
                        .map(|v| format_rational(v, d))
                        .collect::<Vec<_>>()
                })
                .collect();
            PeriodicCandidateOutput {
                profile: formatted_prof,
                maximum_regret: format!("{:.6}", reg),
                maximum_regret_float: reg,
            }
        })
        .collect();

    let output = PeriodicAuditOutput {
        schema: "uniform.periodic-grid-search/v1",
        scope: "all independent periodic profiles on the stated rational grid; regret covers deterministic unilateral policies of the same period",
        game_path: path.to_string_lossy().to_string(),
        game_title: game_json.title,
        denominator: d,
        period: p,
        players: PLAYERS,
        total_profiles,
        evaluated_profiles: total_profiles,
        complete_shard: true,
        complete_global_grid: true,
        elapsed_seconds: elapsed,
        profiles_per_second: speed,
        min_regret_floor: state.min_regret,
        best: best_candidates,
    };

    let json = serde_json::to_string_pretty(&output)?;
    match &args.output {
        Some(out_path) => {
            let mut writer = BufWriter::new(File::create(out_path)?);
            writer.write_all(json.as_bytes())?;
            writer.write_all(b"\n")?;
            eprintln!("Saved certificate to {}", out_path.display());
        }
        None => println!("{json}"),
    }

    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = parse_args()
        .map_err(|message| std::io::Error::new(std::io::ErrorKind::InvalidInput, message))?;

    if let Some(audit_path) = &args.audit_game {
        return run_audit_game(&args, audit_path);
    }

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
            audit_game: None,
            period: 1,
            denominator: 2,
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

    #[test]
    fn candidate_46876_periodic_regret_matches_python() {
        // Candidate 46876 payoffs
        let mut payoffs = [[0.0; PLAYERS]; 16];
        payoffs[1] = [0.0, 4.0, -4.0, -4.0];
        payoffs[2] = [3.0, 3.0, 2.0, -4.0];
        payoffs[3] = [0.0, -1.0, 2.0, 4.0];
        payoffs[4] = [1.0, 4.0, -3.0, 2.0];
        payoffs[5] = [-2.0, -3.0, -3.0, 0.0];
        payoffs[6] = [4.0, -1.0, -4.0, 4.0];
        payoffs[7] = [4.0, -2.0, 1.0, -3.0];
        payoffs[8] = [3.0, 3.0, -3.0, -3.0];
        payoffs[9] = [-3.0, -3.0, -2.0, 4.0];
        payoffs[10] = [0.0, -1.0, 4.0, 3.0];
        payoffs[11] = [-2.0, 2.0, 4.0, 4.0];
        payoffs[12] = [0.0, -2.0, -3.0, -2.0];
        payoffs[13] = [-2.0, 2.0, -1.0, 0.0];
        payoffs[14] = [1.0, -4.0, -1.0, 1.0];
        payoffs[15] = [3.0, -1.0, -3.0, 1.0];

        let continuation = [0.0; PLAYERS];

        // P=1, D=4: 625 profiles. Python computed min regret = 0.75 (3/4)
        let values_d4: Vec<f64> = (0..=4).map(|k| (k as f64) / 4.0).collect();
        let mut min_r_p1 = f64::MAX;
        for idx in 0..625 {
            let prof = decode_profile(idx, 1, &values_d4);
            let r = periodic_profile_regret(&payoffs, &continuation, 1, &prof);
            if r < min_r_p1 {
                min_r_p1 = r;
            }
        }
        assert!((min_r_p1 - 0.75).abs() < 1e-6, "P=1 D=4 min regret must be 0.75, got {min_r_p1}");

        // P=2, D=2: 6561 profiles. Python computed min regret = 1.0
        let values_d2: Vec<f64> = (0..=2).map(|k| (k as f64) / 2.0).collect();
        let mut min_r_p2 = f64::MAX;
        for idx in 0..6561 {
            let prof = decode_profile(idx, 2, &values_d2);
            let r = periodic_profile_regret(&payoffs, &continuation, 2, &prof);
            if r < min_r_p2 {
                min_r_p2 = r;
            }
        }
        assert!((min_r_p2 - 1.0).abs() < 1e-6, "P=2 D=2 min regret must be 1.0, got {min_r_p2}");
    }
}
