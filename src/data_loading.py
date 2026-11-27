"""Load source tables and produce reproducible input quality checks."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT.parent / "Assignment1" / "new_data"
TABLES = ("matches", "deliveries", "match_players", "players", "officials")


def source_data_dir() -> Path:
    """Resolve A1 tables; IPL_DATA_DIR can point to an equivalent directory."""
    return Path(os.environ.get("IPL_DATA_DIR", DEFAULT_DATA_DIR)).expanduser().resolve()


def load_sources() -> dict[str, pd.DataFrame]:
    """Read the five A1 CSV tables without modifying or deduplicating them."""
    data_dir = source_data_dir()
    missing = [name for name in TABLES if not (data_dir / f"{name}.csv").is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing A1 CSV file(s) in {data_dir}: {', '.join(missing)}. "
            "Set IPL_DATA_DIR to the directory containing the five A1 CSVs."
        )
    tables = {name: pd.read_csv(data_dir / f"{name}.csv") for name in TABLES}
    if "date" in tables["matches"]:
        raw_dates = tables["matches"]["date"].astype("string")
        # The source represents a small number of matches with multiple
        # semicolon-separated calendar dates. Use the first as a date anchor.
        first_dates = raw_dates.str.split(";", n=1).str[0]
        parsed_dates = pd.to_datetime(first_dates, errors="coerce")
        invalid = raw_dates.notna() & parsed_dates.isna()
        if invalid.any():
            examples = raw_dates.loc[invalid].head(5).tolist()
            raise ValueError(f"Could not parse match start dates: {examples}")
        tables["matches"].attrs["source_date_text"] = raw_dates
        tables["matches"]["date"] = parsed_dates
    return tables


def quality_rows(tables: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    """Return table-level missingness/duplicate metrics and key-integrity checks."""
    rows: list[dict[str, object]] = []
    for name, frame in tables.items():
        rows.append({
            "scope": name,
            "metric": "table_profile",
            "value": int(len(frame)),
            "details": (
                f"columns={len(frame.columns)}; missing_cells={int(frame.isna().sum().sum())}; "
                f"exact_duplicate_rows={int(frame.duplicated().sum())}"
            ),
        })
        for column in frame.columns:
            missing_count = int(frame[column].isna().sum())
            rows.append({
                "scope": name,
                "metric": f"field_missing:{column}",
                "value": missing_count,
                "details": f"dtype={frame[column].dtype}; missing_pct={100 * missing_count / max(len(frame), 1):.3f}",
            })

    matches = tables["matches"]
    deliveries = tables["deliveries"]
    match_ids = set(matches["match_id"].dropna())
    delivery_ids = set(deliveries["match_id"].dropna())
    roster = tables["match_players"]
    players = tables["players"]
    checks = [
        ("matches.match_id_unique", bool(matches["match_id"].is_unique), f"rows={len(matches)}"),
        ("deliveries_to_matches", len(delivery_ids - match_ids) == 0, f"unmatched_delivery_match_ids={len(delivery_ids - match_ids)}"),
        ("matches_to_deliveries", len(match_ids - delivery_ids) == 0, f"matches_without_delivery_ids={len(match_ids - delivery_ids)}"),
        ("roster_match_ids", len(set(roster.match_id.dropna()) - match_ids) == 0, f"unmatched_roster_match_ids={len(set(roster.match_id.dropna()) - match_ids)}"),
        ("roster_player_ids", len(set(roster.player_id.dropna()) - set(players.player_id.dropna())) == 0, f"unmatched_roster_player_ids={len(set(roster.player_id.dropna()) - set(players.player_id.dropna()))}"),
        ("match_player_natural_key", int(roster.duplicated(["match_id", "player_id"]).sum()) == 0, f"duplicate_pairs={int(roster.duplicated(['match_id', 'player_id']).sum())}"),
    ]
    for label, passed, detail in checks:
        rows.append({"scope": "integrity", "metric": label, "value": bool(passed), "details": detail})

    rows.extend([
        {
            "scope": "matches",
            "metric": "date_range",
            "value": f"{matches.date.min().date()} to {matches.date.max().date()}",
            "details": (
                f"season_labels={matches.season.nunique(dropna=True)}; "
                f"source_rows_chronological={bool(matches.date.is_monotonic_increasing)}; "
                f"multi_calendar_date_entries={int(matches.attrs['source_date_text'].str.contains(';', na=False).sum())}; "
                "date_policy=first listed date used as chronological anchor"
            ),
        },
        {
            "scope": "deliveries",
            "metric": "duplicate_diagnostics",
            "value": int(deliveries.duplicated().sum()),
            "details": (
                f"exact rows repeat; duplicated (match_id, innings, over, ball) rows="
                f"{int(deliveries.duplicated(['match_id', 'innings', 'over', 'ball']).sum())}; "
                "events are retained pending domain-level interpretation"
            ),
        },
        {
            "scope": "deliveries",
            "metric": "run_and_delivery_ranges",
            "value": f"total_runs={deliveries.total_runs.min()}..{deliveries.total_runs.max()}",
            "details": (
                f"innings={deliveries.innings.min()}..{deliveries.innings.max()}; "
                f"over={deliveries.over.min()}..{deliveries.over.max()}; "
                f"super_over_values={sorted(deliveries.super_over.dropna().unique().tolist())}"
            ),
        },
    ])
    return rows
