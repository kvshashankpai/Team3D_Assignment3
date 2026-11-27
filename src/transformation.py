"""Inference-motivated match-state transformation for iteration 2."""

from __future__ import annotations

import pandas as pd


def add_pressure_features(states: pd.DataFrame) -> pd.DataFrame:
    """Add target-relative state fields that are available at the six-over mark."""
    required = {"target_runs", "runs_after_six", "legal_balls_remaining"}
    missing = required - set(states.columns)
    if missing:
        raise ValueError(f"Cannot derive chase pressure; missing {sorted(missing)}")
    transformed = states.copy()
    transformed["runs_remaining"] = transformed.target_runs - transformed.runs_after_six
    transformed["required_run_rate"] = (
        transformed.runs_remaining * 6.0 / transformed.legal_balls_remaining
    )
    if transformed["required_run_rate"].isna().any() or transformed["required_run_rate"].lt(0).any():
        raise ValueError("Invalid required-run-rate values after transformation")
    return transformed
