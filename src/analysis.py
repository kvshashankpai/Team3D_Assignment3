"""Descriptive analysis and uncertainty estimates for the two workflow iterations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rate_interval(successes: int, total: int) -> tuple[float, float]:
    """Wilson 95% interval for a binomial proportion."""
    if total == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * np.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return float(center - half), float(center + half)


def pressure_groups(states: pd.DataFrame) -> pd.DataFrame:
    """Assign equal-frequency required-rate quartiles for descriptive comparison."""
    result = states.copy()
    result["pressure_quartile"] = pd.qcut(
        result.required_run_rate, 4, labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"], duplicates="drop"
    )
    return result


def season_block_bootstrap_difference(
    grouped: pd.DataFrame, iterations: int = 2000, seed: int = 732
) -> tuple[float, float]:
    """95% percentile interval for Q1 minus Q4 win rate, resampling whole seasons."""
    low = grouped.loc[grouped.pressure_quartile.eq("Q1 lowest"), ["season", "chase_success"]]
    high = grouped.loc[grouped.pressure_quartile.eq("Q4 highest"), ["season", "chase_success"]]
    point = float(low.chase_success.mean() - high.chase_success.mean())
    seasons = sorted(grouped.season.unique())
    by_season = {
        season: (
            low.loc[low.season.eq(season), "chase_success"].to_numpy(dtype=float),
            high.loc[high.season.eq(season), "chase_success"].to_numpy(dtype=float),
        )
        for season in seasons
    }
    rng = np.random.default_rng(seed)
    samples: list[float] = []
    for _ in range(iterations):
        chosen = rng.choice(seasons, size=len(seasons), replace=True)
        low_vals = np.concatenate([by_season[s][0] for s in chosen if len(by_season[s][0])])
        high_vals = np.concatenate([by_season[s][1] for s in chosen if len(by_season[s][1])])
        if len(low_vals) and len(high_vals):
            samples.append(float(low_vals.mean() - high_vals.mean()))
    if not samples:
        return float("nan"), float("nan")
    return tuple(float(v) for v in np.quantile(samples, [0.025, 0.975]))


def summarize(states: pd.DataFrame, seed: int = 732) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    """Return actual-data summary, iteration-1 heatmap table, and pressure table."""
    grouped = pressure_groups(states)
    pressure_rows = []
    for label in grouped.pressure_quartile.cat.categories:
        g = grouped.loc[grouped.pressure_quartile.eq(label)]
        n = int(len(g))
        wins = int(g.chase_success.sum())
        lo, hi = _rate_interval(wins, n)
        pressure_rows.append({
            "pressure_quartile": str(label),
            "matches": n,
            "successful_chases": wins,
            "success_rate": wins / n if n else np.nan,
            "wilson_95_low": lo,
            "wilson_95_high": hi,
            "mean_required_run_rate": float(g.required_run_rate.mean()) if n else np.nan,
        })
    pressure_table = pd.DataFrame(pressure_rows)

    low = grouped.loc[grouped.pressure_quartile.eq("Q1 lowest"), "chase_success"]
    high = grouped.loc[grouped.pressure_quartile.eq("Q4 highest"), "chase_success"]
    difference = float(low.mean() - high.mean())
    diff_low, diff_high = season_block_bootstrap_difference(grouped, seed=seed)

    # The initial view uses only raw powerplay runs and wickets, without target context.
    grouped["runs_quartile"] = pd.qcut(
        grouped.runs_after_six, 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
    )
    grouped["wicket_band"] = pd.cut(
        grouped.wickets_lost_after_six,
        bins=[-1, 0, 1, 2, np.inf],
        labels=["0", "1", "2", "3+"],
    )
    heat = grouped.pivot_table(
        index="wicket_band", columns="runs_quartile", values="chase_success", aggfunc="mean", observed=False
    )
    counts = grouped.pivot_table(
        index="wicket_band", columns="runs_quartile", values="chase_success", aggfunc="size", observed=False
    )
    initial_rows = []
    for wicket in heat.index:
        for run_quartile in heat.columns:
            initial_rows.append({
                "wicket_band": str(wicket),
                "runs_quartile": str(run_quartile),
                "success_rate": float(heat.loc[wicket, run_quartile]) if pd.notna(heat.loc[wicket, run_quartile]) else np.nan,
                "matches": int(counts.loc[wicket, run_quartile]) if pd.notna(counts.loc[wicket, run_quartile]) else 0,
            })
    initial_table = pd.DataFrame(initial_rows)

    summary: dict[str, object] = {
        "n_matches": int(len(states)),
        "successful_chases": int(states.chase_success.sum()),
        "unsuccessful_chases": int((states.chase_success == 0).sum()),
        "overall_success_rate": float(states.chase_success.mean()),
        "median_powerplay_runs": float(states.runs_after_six.median()),
        "median_wickets_lost": float(states.wickets_lost_after_six.median()),
        "median_target": float(states.target_runs.median()),
        "pressure_low_high_rate_difference": difference,
        "pressure_difference_ci_95_season_block": [diff_low, diff_high],
        "pressure_q1_success_rate": float(low.mean()),
        "pressure_q4_success_rate": float(high.mean()),
        "pressure_q1_matches": int(len(low)),
        "pressure_q4_matches": int(len(high)),
        "pressure_quartile_method": "equal-frequency quartiles over eligible matches",
        "bootstrap": {"method": "season-block percentile bootstrap", "iterations": 2000, "seed": seed},
    }
    return summary, initial_table, pressure_table
