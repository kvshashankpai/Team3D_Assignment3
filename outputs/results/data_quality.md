# Data Quality and Preprocessing Audit

Source directory: `/Users/shashank/IIITB/sem5/DV/Assignment1/new_data`. Raw data are read only; no raw source file is edited.

## Input structure

| Table | Rows | Columns | Missing cells | Exact duplicate rows |
|---|---:|---:|---:|---:|
| `matches.csv` | 1,243 | 21 | 2,606 | 0 |
| `deliveries.csv` | 295,732 | 22 | 847,065 | 470 |
| `match_players.csv` | 27,909 | 4 | 0 | 0 |
| `players.csv` | 811 | 2 | 0 | 0 |
| `officials.csv` | 6,187 | 3 | 0 | 0 |

## Integrity and ranges

All table-level and key checks are written to `data_quality_summary.csv`. The match and delivery IDs have full two-way coverage. Missing delivery fields are concentrated in event-specific columns (for example, wicket and fielder fields); they are not imputed for the chase-state analysis. Match metadata contains optional missing city/method/result fields.
Per-field missing counts, percentages, and inferred pandas dtypes are also recorded in the CSV. Two source records list multiple calendar dates separated by semicolons; the first listed date is used as a chronological date anchor, not as a model feature. Source match rows are not fully chronological; the analysis state table is sorted by date and match ID before splitting.
Delivery value ranges: `{"innings": [1, 6], "match_overs": [20, 20], "over": [0, 19], "required_run_rate": [0.7857142857142857, 15.857142857142858], "runs_after_six": [14, 116], "target_runs": [68, 288], "total_runs": [0, 7]}`.
Distribution and outlier diagnostics (Tukey fences are descriptive flags, not exclusions):

| Field (unit) | Min | P01 | Median | P99 | Max | Tukey-fence rows |
|---|---:|---:|---:|---:|---:|---:|
| delivery total_runs (runs/event) | 0.00 | 0.00 | 1.00 | 6.00 | 7.00 | 52,219 |
| target_runs (runs/match) | 68.00 | 90.93 | 169.00 | 255.07 | 288.00 | 24 |
| runs_after_six (runs/match) | 14.00 | 21.00 | 48.00 | 89.07 | 116.00 | 19 |
| wickets_lost_after_six (wickets/match) | 0.00 | 0.00 | 1.00 | 5.00 | 6.00 | 63 |
| required_run_rate (runs/over) | 0.79 | 2.63 | 8.64 | 14.15 | 15.86 | 27 |
Units are runs per delivery, runs per match, wickets per match, and runs per over. Every match has 20 scheduled overs in this source. Spatial validity is not applicable to the selected IPL question; venues are categorical and are not used as coordinates.
Eligibility and row counts: `{"d_l_method_matches": 23, "eligible_states": 1194, "matches_input": 1243, "matches_with_first_innings": 1243, "matches_with_second_innings_six_over_data": 1237, "matches_with_short_scheduled_overs": 0, "normal_result_with_winner": 1218, "rows_with_target_reached_by_six_overs": 0, "second_innings_multi_batting_team_in_powerplay": 0, "second_innings_with_at_least_36_legal_balls_in_powerplay": 1228, "state_date_max": "2026-05-31", "state_date_min": "2008-04-18", "successful_chases": 649, "unsuccessful_chases": 545}`.
The delivery table contains exact repeated event rows and repeated `(match_id, innings, over, ball)` keys. Some examples are repeated wide events with matching batter, bowler, and run fields; a repeated index can also represent multiple delivery events within an over. Because event identity cannot be resolved from the provided columns alone, rows are retained and flagged rather than blindly deduplicated. This may preserve a source-data duplication if one exists; it is a limitation.
No observations were removed for being outliers. The state dataset is filtered only by match eligibility and a fully observed six-over checkpoint, as defined in `PLAN.md`.

## Preprocessing decisions

1. Exclude super-over deliveries so the target and checkpoint represent the regulation chase.
2. Use only normal matches with a recorded winner; omit ties and no-results because a binary chase outcome is ambiguous.
3. Omit D/L matches because the revised target is not recoverable from first-innings runs alone.
4. Require a scheduled match of at least seven overs and at least 36 legal deliveries in overs 0–5. A match that ends before the six-over decision point cannot be treated as a prediction made at that point.
5. Define target as first-innings total runs plus one; total runs include recorded batter runs and extras.
6. Define legal deliveries as rows with zero wides and zero no-balls. Sum all six-over delivery runs and recorded wickets; do not discard wides/no-balls from runs or wickets.
7. Define chase success as the second-innings batting team matching the official match winner.
8. Add runs remaining and required run rate in iteration 2: `(target − six-over runs) × 6 / legal balls remaining`. The denominator comes from the match's scheduled overs.

## Leakage and scope

The winner is used only to construct the label and evaluate predictions. Iteration 1 predictors use only the six-over runs and wickets. Iteration 2 adds target and checkpoint-derived pressure features that are known at that point in the chase. Standardization is fit on training rows only. Later match dates form the test set.
The analysis describes association and held-out prediction; it does not estimate causal effects. Repeated matches within seasons and changing rules, teams, schedules, and formats may limit generalization.
