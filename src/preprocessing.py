"""Create one eligible, match-level chase state at the six-over mark."""

from __future__ import annotations

import pandas as pd


REQUIRED_MATCH_COLUMNS = {"match_id", "date", "season", "winner", "result", "method", "overs"}
REQUIRED_DELIVERY_COLUMNS = {
    "match_id", "innings", "over", "total_runs", "wides", "noballs", "wicket",
    "batting_team", "bowling_team", "super_over",
}


def build_chase_states(
    matches: pd.DataFrame, deliveries: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Aggregate first-innings target and second-innings state after six overs.

    All original delivery rows are retained. No duplicate removal or outlier trimming occurs.
    """
    missing_m = REQUIRED_MATCH_COLUMNS - set(matches.columns)
    missing_d = REQUIRED_DELIVERY_COLUMNS - set(deliveries.columns)
    if missing_m or missing_d:
        raise ValueError(f"Missing columns: matches={sorted(missing_m)}, deliveries={sorted(missing_d)}")

    regular = deliveries.loc[deliveries.super_over.fillna(0).eq(0)].copy()
    first = regular.loc[regular.innings.eq(1)].groupby("match_id", as_index=False).agg(
        first_innings_runs=("total_runs", "sum")
    )
    second = regular.loc[regular.innings.eq(2)].copy()
    pp = second.loc[second.over.lt(6)].copy()
    pp["legal_ball"] = pp.wides.fillna(0).eq(0) & pp.noballs.fillna(0).eq(0)
    states = pp.groupby("match_id", as_index=False).agg(
        runs_after_six=("total_runs", "sum"),
        wickets_lost_after_six=("wicket", "sum"),
        legal_balls_after_six=("legal_ball", "sum"),
        batting_team=("batting_team", "first"),
        batting_team_count=("batting_team", "nunique"),
    )
    frame = matches.merge(first, on="match_id", how="left", validate="one_to_one")
    frame = frame.merge(states, on="match_id", how="left", validate="one_to_one")

    counts: dict[str, object] = {
        "matches_input": int(len(matches)),
        "matches_with_first_innings": int(frame.first_innings_runs.notna().sum()),
        "matches_with_second_innings_six_over_data": int(frame.runs_after_six.notna().sum()),
        "normal_result_with_winner": int((frame.result.eq("normal") & frame.winner.notna()).sum()),
        "d_l_method_matches": int(frame.method.notna().sum()),
        "matches_with_short_scheduled_overs": int(frame.overs.lt(7).sum()),
        "second_innings_with_at_least_36_legal_balls_in_powerplay": int(frame.legal_balls_after_six.ge(36).sum()),
        "second_innings_multi_batting_team_in_powerplay": int(frame.batting_team_count.fillna(0).gt(1).sum()),
    }

    eligible = (
        frame.result.eq("normal")
        & frame.winner.notna()
        & frame.method.isna()
        & frame.overs.ge(7)
        & frame.first_innings_runs.notna()
        & frame.legal_balls_after_six.ge(36)
        & frame.batting_team.notna()
        & frame.batting_team_count.eq(1)
    )
    selected = frame.loc[eligible].copy()
    selected["target_runs"] = selected.first_innings_runs.astype(int) + 1
    selected["chase_success"] = selected.winner.eq(selected.batting_team).astype(int)
    selected["season"] = selected.season.astype(str)
    selected["match_date"] = pd.to_datetime(selected.date, errors="coerce")
    selected["scheduled_legal_balls"] = selected.overs.astype(int) * 6
    selected["legal_balls_remaining"] = selected.scheduled_legal_balls - selected.legal_balls_after_six.astype(int)
    selected = selected.loc[selected.legal_balls_remaining.gt(0)].copy()
    selected["runs_remaining"] = selected.target_runs - selected.runs_after_six.astype(int)
    selected["required_run_rate"] = (
        selected.runs_remaining * 6.0 / selected.legal_balls_remaining
    )

    # Match winner must correspond to one of the two sides in the delivery records.
    teams_by_match = regular.groupby("match_id").agg(
        delivery_teams=("batting_team", lambda s: set(s.dropna()))
    )
    side_teams = teams_by_match.delivery_teams.reindex(selected.match_id).tolist()
    selected["winner_is_delivery_team"] = [w in ts for w, ts in zip(selected.winner, side_teams)]
    if not selected.winner_is_delivery_team.all():
        bad = selected.loc[~selected.winner_is_delivery_team, "match_id"].astype(str).tolist()
        raise ValueError(f"Winner/team integrity failed for match IDs: {bad[:10]}")
    if selected.runs_remaining.le(0).any():
        bad = selected.loc[selected.runs_remaining.le(0), "match_id"].astype(str).tolist()
        raise ValueError(f"Nonpositive runs remaining at completed six-over checkpoint: {bad[:10]}")

    keep = [
        "match_id", "match_date", "season", "batting_team", "winner", "overs",
        "target_runs", "runs_after_six", "wickets_lost_after_six", "legal_balls_after_six",
        "legal_balls_remaining", "runs_remaining", "required_run_rate", "chase_success",
    ]
    selected = selected[keep].sort_values(["match_date", "match_id"]).reset_index(drop=True)
    counts["eligible_states"] = int(len(selected))
    counts["successful_chases"] = int(selected.chase_success.sum())
    counts["unsuccessful_chases"] = int((selected.chase_success == 0).sum())
    counts["state_date_min"] = str(selected.match_date.min().date())
    counts["state_date_max"] = str(selected.match_date.max().date())
    counts["rows_with_target_reached_by_six_overs"] = int(selected.runs_remaining.le(0).sum())
    return selected, counts
