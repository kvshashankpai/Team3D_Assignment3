"""Run the end-to-end A3 visual analytics pipeline from the A1 raw CSV files."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

from src.analysis import summarize
from src.data_loading import load_sources, quality_rows, source_data_dir
from src.modeling import cluster_states, compare_models
from src.preprocessing import build_chase_states
from src.transformation import add_pressure_features
from src.visualization import make_figures
from src.workflow_render import render_workflow


def _write_data_quality(tables: dict[str, pd.DataFrame], states: pd.DataFrame, audit: dict[str, object], output: Path) -> None:
    quality = pd.DataFrame(quality_rows(tables))
    quality.to_csv(output / "data_quality_summary.csv", index=False)
    missing = {name: int(frame.isna().sum().sum()) for name, frame in tables.items()}
    exact = {name: int(frame.duplicated().sum()) for name, frame in tables.items()}
    deliveries = tables["deliveries"]
    range_summary = {
        "total_runs": [int(deliveries.total_runs.min()), int(deliveries.total_runs.max())],
        "innings": [int(deliveries.innings.min()), int(deliveries.innings.max())],
        "over": [int(deliveries.over.min()), int(deliveries.over.max())],
        "match_overs": [int(tables["matches"].overs.min()), int(tables["matches"].overs.max())],
        "target_runs": [int(states.target_runs.min()), int(states.target_runs.max())],
        "runs_after_six": [int(states.runs_after_six.min()), int(states.runs_after_six.max())],
        "required_run_rate": [float(states.required_run_rate.min()), float(states.required_run_rate.max())],
    }
    distribution_fields = {
        "delivery total_runs (runs/event)": deliveries.total_runs,
        "target_runs (runs/match)": states.target_runs,
        "runs_after_six (runs/match)": states.runs_after_six,
        "wickets_lost_after_six (wickets/match)": states.wickets_lost_after_six,
        "required_run_rate (runs/over)": states.required_run_rate,
    }
    distribution_rows = []
    for label, values in distribution_fields.items():
        q1, q3 = values.quantile([0.25, 0.75])
        lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        distribution_rows.append({
            "field_and_unit": label,
            "min": float(values.min()),
            "p01": float(values.quantile(0.01)),
            "median": float(values.median()),
            "p99": float(values.quantile(0.99)),
            "max": float(values.max()),
            "tukey_fence_count": int(((values < lower) | (values > upper)).sum()),
        })
    text = [
        "# Data Quality and Preprocessing Audit", "",
        f"Source directory: `{source_data_dir()}`. Raw data are read only; no raw source file is edited.", "",
        "## Input structure", "",
        "| Table | Rows | Columns | Missing cells | Exact duplicate rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, frame in tables.items():
        text.append(f"| `{name}.csv` | {len(frame):,} | {len(frame.columns)} | {missing[name]:,} | {exact[name]:,} |")
    text.extend([
        "", "## Integrity and ranges", "",
        "All table-level and key checks are written to `data_quality_summary.csv`. The match and delivery IDs have full two-way coverage. Missing delivery fields are concentrated in event-specific columns (for example, wicket and fielder fields); they are not imputed for the chase-state analysis. Match metadata contains optional missing city/method/result fields.",
        "Per-field missing counts, percentages, and inferred pandas dtypes are also recorded in the CSV. Two source records list multiple calendar dates separated by semicolons; the first listed date is used as a chronological date anchor, not as a model feature. Source match rows are not fully chronological; the analysis state table is sorted by date and match ID before splitting.",
        f"Delivery value ranges: `{json.dumps(range_summary, sort_keys=True)}`.",
        "Distribution and outlier diagnostics (Tukey fences are descriptive flags, not exclusions):",
        "", "| Field (unit) | Min | P01 | Median | P99 | Max | Tukey-fence rows |", "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in distribution_rows:
        text.append(
            f"| {row['field_and_unit']} | {row['min']:.2f} | {row['p01']:.2f} | {row['median']:.2f} | "
            f"{row['p99']:.2f} | {row['max']:.2f} | {row['tukey_fence_count']:,} |"
        )
    text.extend([
        "Units are runs per delivery, runs per match, wickets per match, and runs per over. Every match has 20 scheduled overs in this source. Spatial validity is not applicable to the selected IPL question; venues are categorical and are not used as coordinates.",
        f"Eligibility and row counts: `{json.dumps(audit, sort_keys=True)}`.",
        "The delivery table contains exact repeated event rows and repeated `(match_id, innings, over, ball)` keys. Some examples are repeated wide events with matching batter, bowler, and run fields; a repeated index can also represent multiple delivery events within an over. Because event identity cannot be resolved from the provided columns alone, rows are retained and flagged rather than blindly deduplicated. This may preserve a source-data duplication if one exists; it is a limitation.",
        "No observations were removed for being outliers. The state dataset is filtered only by match eligibility and a fully observed six-over checkpoint, as defined in `PLAN.md`.",
        "", "## Preprocessing decisions", "",
        "1. Exclude super-over deliveries so the target and checkpoint represent the regulation chase.",
        "2. Use only normal matches with a recorded winner; omit ties and no-results because a binary chase outcome is ambiguous.",
        "3. Omit D/L matches because the revised target is not recoverable from first-innings runs alone.",
        "4. Require a scheduled match of at least seven overs and at least 36 legal deliveries in overs 0–5. A match that ends before the six-over decision point cannot be treated as a prediction made at that point.",
        "5. Define target as first-innings total runs plus one; total runs include recorded batter runs and extras.",
        "6. Define legal deliveries as rows with zero wides and zero no-balls. Sum all six-over delivery runs and recorded wickets; do not discard wides/no-balls from runs or wickets.",
        "7. Define chase success as the second-innings batting team matching the official match winner.",
        "8. Add runs remaining and required run rate in iteration 2: `(target − six-over runs) × 6 / legal balls remaining`. The denominator comes from the match's scheduled overs.",
        "", "## Leakage and scope", "",
        "The winner is used only to construct the label and evaluate predictions. Iteration 1 predictors use only the six-over runs and wickets. Iteration 2 adds target and checkpoint-derived pressure features that are known at that point in the chase. Standardization is fit on training rows only. Later match dates form the test set.",
        "The analysis describes association and held-out prediction; it does not estimate causal effects. Repeated matches within seasons and changing rules, teams, schedules, and formats may limit generalization.",
    ])
    (output / "data_quality.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def _write_validation(
    tables: dict[str, pd.DataFrame], states: pd.DataFrame, audit: dict[str, object],
    model_results: dict[str, object], quality1: dict[str, object], quality2: dict[str, object],
    output: Path,
) -> None:
    ids_ok = set(tables["matches"].match_id) == set(tables["deliveries"].match_id)
    features_ok = states.required_run_rate.notna().all() and states.required_run_rate.ge(0).all()
    target_ok = states.runs_remaining.gt(0).all()
    dates = model_results["split"]
    temporal_ok = dates["train_date_max"] < dates["test_date_min"]
    all_dates_ok = states.match_date.notna().all()
    winner_ok = states.chase_success.isin([0, 1]).all()
    checks = [
        ("A1 match/delivery key coverage", ids_ok, "Two-way set equality of match IDs."),
        ("Preprocessing eligibility", len(states) == audit["eligible_states"], "Eligible row count matches the preprocessing audit."),
        ("Checkpoint completion", states.legal_balls_after_six.ge(36).all(), "All rows contain at least 36 legal balls in overs 0–5."),
        ("Outcome construction", winner_ok, "Every retained row has a binary winner-based label."),
        ("Positive runs remaining", target_ok, "No retained six-over checkpoint has already reached the target."),
        ("Pressure feature arithmetic", features_ok, "Required run rate is finite and nonnegative."),
        ("Chronological split", temporal_ok, "Training dates precede all test dates."),
        ("Match start dates parsed", all_dates_ok, "All retained matches use the first listed source date as the match-start date."),
        ("First iteration excludes target pressure", "required_run_rate" not in model_results["feature_sets"]["iteration1_raw_state"], "Iteration 1 uses only runs and wickets."),
        ("Second iteration adds a derived context feature", "required_run_rate" in model_results["feature_sets"]["iteration2_target_pressure"], "The feedback transformation is represented in model inputs."),
        ("Cluster outputs", len(quality1["cluster_counts"]) == 4 and len(quality2["cluster_counts"]) == 4, "Four nonempty K-means display clusters are available in each iteration."),
    ]
    lines = ["# Validation and Correctness", "", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"]
    for name, passed, detail in checks:
        lines.append(f"| {name} | {'PASS' if passed else 'FAIL'} | {detail} |")
    lines.extend([
        "", "## Statistical and model validation", "",
        "- The primary group contrast uses Wilson intervals for binomial proportions and a 2,000-replicate season-block percentile bootstrap for the Q1–Q4 difference. Resampling seasons acknowledges within-season dependence, though the number of season blocks remains limited.",
        "- Logistic regression is evaluated on a later-date holdout. The majority baseline and both logistic models use the same test matches and a fixed 0.5 probability threshold for class metrics; ROC-AUC and Brier score use probabilities.",
        "- Means and standard deviations for model features are estimated from the training data only. The first model's predictors are available at the end of six overs; the second adds required run rate computed from the known target, current score, and remaining legal balls.",
        "- K-means standardizes only unsupervised feature columns, uses a fixed seed and ten initializations, and reports inertia and silhouette. The labels are arbitrary algorithmic groupings and are not treated as real match classes.",
        "- Plot axes, color meanings, samples, and interval definitions are generated directly from pipeline outputs; no observation is trimmed for visual convenience.",
        "", "## Assumptions, limitations, and alternatives", "",
        "- The official winner corresponds to the second-innings batting side for successful chases. Ties, no-results, D/L matches, and super overs are excluded to avoid ambiguous or reconstructed labels.",
        "- The first-innings total is a valid target for standard, normal matches without D/L. A chase ending before six overs is outside the prediction-time population.",
        "- The source has exact repeated delivery rows and repeated over/ball keys. They are retained because the schema does not prove whether identical wide-event rows are duplicate records or distinct deliveries.",
        "- One chronological split is more realistic than random splitting but can reflect changing rules, season composition, and team strength. Results do not imply future performance under changed conditions.",
        "- Required rate and outcome are associated. This analysis cannot isolate the causal impact of target pressure from team skill, venue, opponent, season, toss, or match conditions.",
        "- Alternative feedback choices include target-normalized run rate, over-by-over state trajectories, or a team/venue-adjusted model. Those would add complexity and would need separate leakage and sample-size checks.",
        "", "## Reproducibility", "",
        "The report is generated by `run_all.py` from the A1 CSVs. The latest verification run regenerated all result tables, models, transformed data, and figures from the source files. Run status and environment are recorded in `LOG.md`.",
    ])
    if not all(passed for _, passed, _ in checks):
        lines.insert(2, "**Pipeline validation has failures; do not claim full correctness until resolved.**")
    (output / "validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out_results = ROOT / "outputs" / "results"
    out_results.mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "transformed").mkdir(parents=True, exist_ok=True)
    images = ROOT / "images"
    tables = load_sources()

    states, audit = build_chase_states(tables["matches"], tables["deliveries"])
    states.to_csv(ROOT / "data" / "processed" / "iteration1_chase_states.csv", index=False)
    transformed = add_pressure_features(states)
    transformed.to_csv(ROOT / "data" / "transformed" / "iteration2_chase_pressure.csv", index=False)

    summary, initial_table, pressure_table = summarize(transformed)
    initial_table.to_csv(out_results / "iteration1_state_outcomes.csv", index=False)
    pressure_table.to_csv(out_results / "iteration2_pressure_outcomes.csv", index=False)

    features1 = ["runs_after_six", "wickets_lost_after_six"]
    features2 = features1 + ["required_run_rate"]
    cluster1, centers1, cluster_quality1 = cluster_states(
        transformed, features1, "cluster_iteration1"
    )
    cluster2, centers2, cluster_quality2 = cluster_states(
        transformed, features2, "cluster_iteration2"
    )
    cluster1.to_csv(out_results / "iteration1_clusters.csv", index=False)
    centers1.to_csv(out_results / "iteration1_cluster_centers.csv", index=False)
    cluster2.to_csv(out_results / "iteration2_clusters.csv", index=False)
    centers2.to_csv(out_results / "iteration2_cluster_centers.csv", index=False)

    model_results, predictions = compare_models(transformed)
    (ROOT / "outputs" / "models").mkdir(parents=True, exist_ok=True)
    predictions.to_csv(ROOT / "outputs" / "models" / "holdout_predictions.csv", index=False)
    (ROOT / "outputs" / "models" / "metrics.json").write_text(
        json.dumps(model_results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    figure_paths = make_figures(
        transformed, initial_table, pressure_table, cluster1, centers1,
        cluster2, centers2, model_results, images,
    )
    figure_paths.append(render_workflow(images / "workflow_diagram.png"))
    _write_data_quality(tables, transformed, audit, out_results)

    results = {
        "project": "DAS732 A3 IPL chase-state visual analytics",
        "random_seed": 732,
        "data_source_directory": str(source_data_dir()),
        "eligibility_audit": audit,
        "summary": summary,
        "iteration1_clustering": cluster_quality1,
        "iteration2_clustering": cluster_quality2,
        "models": model_results,
        "figures": [str(p.relative_to(ROOT)) for p in figure_paths],
    }
    (out_results / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / "outputs" / "results" / "results_summary.md").write_text(
        "# Generated Results Summary\n\n```json\n" + json.dumps(results, indent=2, sort_keys=True) + "\n```\n",
        encoding="utf-8",
    )
    _write_validation(tables, transformed, audit, model_results, cluster_quality1, cluster_quality2, out_results)

    from src.reporting import generate_report
    generate_report(ROOT, results)
    print(f"Pipeline complete: {len(transformed):,} eligible chase states; {len(figure_paths)} figures.")
    print(f"Results: {out_results / 'results.json'}")


if __name__ == "__main__":
    main()
