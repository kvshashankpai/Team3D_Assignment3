"""Report-ready visualizations for both iterations of the chase-state workflow."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


NAVY = "#17324D"
TEAL = "#158A8A"
CORAL = "#D76C5B"
PALE = "#EDF3F6"
GOLD = "#E5AF3B"


def _style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelcolor": NAVY,
        "text.color": NAVY,
        "axes.edgecolor": "#AAB7C1",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })


def _save(fig: plt.Figure, folder: Path, name: str) -> None:
    fig.savefig(folder / name, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_figures(
    states: pd.DataFrame,
    initial_table: pd.DataFrame,
    pressure_table: pd.DataFrame,
    clusters1: pd.DataFrame,
    centers1: pd.DataFrame,
    clusters2: pd.DataFrame,
    centers2: pd.DataFrame,
    model_results: dict[str, object],
    folder: Path,
) -> list[Path]:
    """Create five 240-dpi figures used by the report and demo."""
    folder.mkdir(parents=True, exist_ok=True)
    _style()
    outputs: list[Path] = []

    # Figure 1: first iteration, before encoding target pressure.
    wickets = ["0", "1", "2", "3+"]
    runs = ["Q1", "Q2", "Q3", "Q4"]
    rates = initial_table.pivot(index="wicket_band", columns="runs_quartile", values="success_rate").reindex(index=wickets, columns=runs)
    counts = initial_table.pivot(index="wicket_band", columns="runs_quartile", values="matches").reindex(index=wickets, columns=runs)
    values = rates.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(values)
    fig, ax = plt.subplots(figsize=(8.2, 4.7), constrained_layout=True)
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#E5E9EC")
    im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(runs)), runs)
    ax.set_yticks(range(len(wickets)), wickets)
    ax.set_xlabel("Powerplay runs, equal-frequency quartile")
    ax.set_ylabel("Wickets lost by the end of six overs")
    ax.set_title("Iteration 1 | Chase success by raw six-over state", loc="left", pad=12)
    for i in range(len(wickets)):
        for j in range(len(runs)):
            if np.isfinite(values[i, j]):
                n = counts.iloc[i, j]
                ax.text(j, i, f"{values[i, j]:.0%}\n(n={int(n)})", ha="center", va="center",
                        color="white" if values[i, j] > 0.62 else NAVY, fontsize=9, fontweight="bold")
            else:
                ax.text(j, i, "—", ha="center", va="center", color="#687985", fontsize=11)
    cb = fig.colorbar(im, ax=ax, shrink=0.82, pad=0.03)
    cb.set_label("Observed chase-success share")
    outputs.append(folder / "iteration1_state_outcomes.png")
    _save(fig, folder, outputs[-1].name)

    # Figure 2: unsupervised first-iteration state groups.
    c1 = clusters1.merge(states[["match_id", "runs_after_six", "wickets_lost_after_six"]], on="match_id", validate="one_to_one")
    fig, ax = plt.subplots(figsize=(8.2, 5.0), constrained_layout=True)
    palette = ["#537AA5", "#49A397", "#E2AA45", "#D76C5B"]
    for cluster, group in c1.groupby("cluster_iteration1"):
        ax.scatter(group.runs_after_six, group.wickets_lost_after_six, s=21, alpha=0.48,
                   color=palette[int(cluster) - 1], label=f"Cluster {int(cluster)} (n={len(group)})", linewidths=0)
    ax.scatter(centers1.runs_after_six, centers1.wickets_lost_after_six, marker="X", s=150,
               color=NAVY, edgecolor="white", linewidth=1.2, label="Cluster centers", zorder=5)
    ax.set_xlabel("Runs scored in overs 0–5")
    ax.set_ylabel("Wickets lost in overs 0–5")
    ax.set_title("Iteration 1 | K-means groups on raw chase state", loc="left", pad=12)
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="best")
    outputs.append(folder / "iteration1_clusters.png")
    _save(fig, folder, outputs[-1].name)

    # Figure 3: target-pressure gradient and interval.
    fig, ax = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    x = np.arange(len(pressure_table))
    y = pressure_table.success_rate.to_numpy(dtype=float)
    lower = y - pressure_table.wilson_95_low.to_numpy(dtype=float)
    upper = pressure_table.wilson_95_high.to_numpy(dtype=float) - y
    bars = ax.bar(x, y, color=["#2B9A8F", "#6DB7A5", "#E7B54A", "#D76C5B"], width=0.62, zorder=2)
    ax.errorbar(x, y, yerr=np.vstack([lower, upper]), fmt="none", ecolor=NAVY, capsize=4, lw=1.5, zorder=3)
    for i, bar in enumerate(bars):
        n = int(pressure_table.iloc[i].matches)
        ax.text(bar.get_x() + bar.get_width() / 2, min(0.98, y[i] + upper[i] + 0.035), f"n={n}",
                ha="center", va="bottom", fontsize=8, color=NAVY)
    ax.set_xticks(x, pressure_table.pressure_quartile.astype(str))
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Successful chase share")
    ax.set_xlabel("Required run rate after six overs (quartiles, low to high)")
    ax.set_title("Iteration 2 | Target pressure separates chase outcomes", loc="left", pad=12)
    ax.grid(axis="y", color="#E3E9ED", linewidth=0.8, zorder=0)
    outputs.append(folder / "iteration2_pressure_outcomes.png")
    _save(fig, folder, outputs[-1].name)

    # Figure 4: target-aware unsupervised representation.
    c2 = clusters2.merge(states[["match_id", "runs_after_six", "required_run_rate"]], on="match_id", validate="one_to_one")
    fig, ax = plt.subplots(figsize=(8.2, 5.0), constrained_layout=True)
    for cluster, group in c2.groupby("cluster_iteration2"):
        ax.scatter(group.runs_after_six, group.required_run_rate, s=22, alpha=0.48,
                   color=palette[int(cluster) - 1], label=f"Cluster {int(cluster)} (n={len(group)})", linewidths=0)
    ax.scatter(centers2.runs_after_six, centers2.required_run_rate, marker="X", s=150,
               color=NAVY, edgecolor="white", linewidth=1.2, label="Cluster centers", zorder=5)
    ax.set_xlabel("Runs scored in overs 0–5")
    ax.set_ylabel("Required run rate after six overs")
    ax.set_title("Iteration 2 | K-means groups after adding target pressure", loc="left", pad=12)
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="best")
    outputs.append(folder / "iteration2_clusters.png")
    _save(fig, folder, outputs[-1].name)

    # Figure 5: held-out model comparison.
    models = model_results["models"]
    keys = ["majority_baseline_probability", "iteration1_raw_state", "iteration2_target_pressure"]
    labels = ["Majority\nbaseline", "Raw state\n(logistic)", "Target-aware\n(logistic)"]
    metrics = ["accuracy", "f1", "roc_auc"]
    colors = ["#537AA5", "#49A397", "#D76C5B"]
    fig, ax = plt.subplots(figsize=(9.2, 5.2), constrained_layout=True)
    positions = np.arange(len(keys))
    width = 0.23
    for j, metric in enumerate(metrics):
        vals = [float(models[key][metric]) for key in keys]
        bars = ax.bar(positions + (j - 1) * width, vals, width, color=colors[j], label=metric.replace("_", " ").title())
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    ax.set_xticks(positions, labels)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score on later-date test matches")
    ax.set_title("Held-out prediction | Does target pressure add useful information?", loc="left", pad=12)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.grid(axis="y", color="#E3E9ED", linewidth=0.8, zorder=0)
    outputs.append(folder / "model_comparison.png")
    _save(fig, folder, outputs[-1].name)

    return outputs
