# A3 Analytical and Design Plan

## Scope and source-of-truth files

The official assignment prompt is `DAS732_T1-26-27_A3.pdf` in this project. It requires statistical analysis, classical data mining, supervised machine learning, a Keim-style visual analytics workflow with an inference-triggered data transformation and a second visualization iteration, and a report, image folder, and video demo. The workflow diagram must unroll the feedback path and label its edge `Feedback loop`. The A1 report belongs in the A3 report appendix and is not assessed as A3 work. The VAST 2026 challenge cannot replace these tasks.

The inspected project sources are in sibling folders `../Assignment1` and `../Assignment2`. A1's IPL files and Tableau workbook/report are the core source. A2's gridMET daily climate slice and visualization scripts are unrelated to this IPL question, so they will not be added as supplementary data. The pipeline will read A1 source files in place and will not duplicate the large raw tables. The A1 report PDF will be copied into the A3 report appendix so the A3 submission can stand alone.

Two different A1 CSV snapshots are present: `Assignment1/data/` (1,158 matches with `M0001`-style IDs and a different schema) and `Assignment1/new_data/` (1,243 matches, matching the A1 report's table counts). Their match IDs do not overlap, so they are not merged. The newer `new_data` snapshot is selected because its structure and row counts match the A1 report and Tableau story materials. A2's `Member1/correct_data/` duplicates that selected snapshot and is not a separate data source.

## Inventory findings and inherited work

- A1 source tables: `matches.csv` (1,243 rows, 21 columns), `deliveries.csv` (295,732 rows, 22 columns), `match_players.csv` (27,909 rows, 4 columns), `players.csv` (811 rows, 2 columns), and `officials.csv` (6,187 rows, 3 columns), under `../Assignment1/new_data/`.
- A1 also contains a Tableau workbook, a 21-page report, a two-page A1 prompt, a story-plan PDF, and a video. Its report covers 15 visualizations spanning IPL scoring, toss/chasing, team performance, batting, bowling, and venues. Reuse those data definitions and visual context where valid; A3 adds match-state analysis and predictive modeling, rather than presenting the old charts as new work.
- A2 contains a January–March 2020 gridMET NetCDF slice, sampled days, image outputs, and preparation/visualization scripts. This establishes a separate geospatial/scientific visualization context but does not strengthen an IPL chase-state analysis.
- The A1 match table spans 2008-04-18 through 2026-05-31 and 19 season labels. All match IDs in deliveries resolve to matches and vice versa. A1 report describes the same overall source tables and story; the report's numerical claims will not be reused as A3 results without pipeline verification.
- Quick feasibility check: after restricting to the second innings, regular deliveries, at least 36 legal balls in overs 0–5, standard-length (at least seven-over) matches, normal resolved results, and no D/L method, 1,194 match-level powerplay states remain. Outcomes are 649 successful chases and 545 unsuccessful chases. The exact filters and counts will be recomputed and emitted by the pipeline.

## Candidate data stories

Scores below are out of 5 in this order: dataset relevance, analytical depth, visualization potential, feasibility, feedback-loop strength, interpretability, demo suitability. Feasibility checks used actual files: the A1 match and delivery tables, their date/season coverage, and the existing A1 report/workbook. The chosen story also received a quantitative check on 1,194 eligible chase states: the observed chase-success share falls from about 86.8% in the lowest required-rate quartile to 16.1% in the highest. These are scoping checks, not final reported outputs; pipeline results will be authoritative.

| Candidate | Question and reason it matters | Data can answer | Planned views and methods | Iteration-1 inference → transformation → iteration-2 question | Scores / 35 |
|---|---|---|---|---|---:|
| **A. Chase pressure at the six-over mark (selected)** | How do the score and wickets after six overs relate to eventual chase success, and how does the first-innings target change that interpretation? This describes a familiar strategic decision point without claiming causality. | Match targets from first-innings deliveries, second-innings state from deliveries in overs 0–5, and the eventual match winner. | Distribution and outcome-rate plots; confidence intervals for extreme pressure groups; unsupervised K-means on standardized chase-state features; a majority-class baseline and logistic regression using only six-over state features, evaluated on a chronological holdout. | If equivalent-looking score/wicket states have materially different success rates as the remaining required rate changes, derive required runs per over from target minus score and remaining legal balls. Revisualize and compare a target-aware model and state clusters. | 5, 5, 5, 5, 5, 5, 5 = **35** |
| B. Scoring environment through IPL seasons | How have scoring rates and innings distributions changed over time? This places A1's league-wide scoring story in a statistical context. | Season/date, innings total, delivery runs, and phases from A1 tables; the 19-season span is adequate for temporal displays. | Seasonal run-rate lines, score distributions, phase comparisons, robust trend summaries, and season clustering. | If league averages obscure distinct eras or conditions, segment seasons or normalize by innings/phase, then compare the era distributions. | 5, 3, 5, 5, 3, 5, 4 = 30 |
| C. Team scoring profiles and outcomes | Which team scoring profiles are associated with stronger match outcomes? This extends A1 team/phase views into a profile analysis. | Team, season, deliveries, match result, and phase measures are present; A1 already normalizes historical aliases and has team-season visualizations. | Team-phase heatmaps, profile clustering, association analysis, and an outcome model. | If one phase dominates team summaries, segment by season or opponent strength and revisualize team profiles. | 5, 4, 5, 4, 3, 3, 4 = 28 |

### Selection rationale

Candidate A is selected because it gives one concrete, time-bounded research question, uses event and match data already present, provides a valid binary target (successful chase) without inventing labels, supports both clustering and supervised prediction, and leads naturally to a derived match-state feature. It is also explainable in a short demo: one first-iteration view suggests the missing context, the target-pressure calculation encodes that context, and a second view/model checks the change. Candidate B would largely repeat A1's story and offer a weaker transformation. Candidate C has more aggregation and franchise-comparability choices and a less direct feedback trigger.

## Final research question and boundaries

**Research question:** At the end of six completed legal overs in a standard IPL second innings, how do runs and wickets relate to eventual chase success, and how much additional explanatory/predictive information comes from the required scoring rate implied by the first-innings target?

The unit of analysis is one match's second-innings state at the end of overs 0–5. The outcome is whether the second-innings batting team is the official winner. The analysis excludes super-over deliveries, tied/no-result matches, D/L-affected matches whose revised target cannot be reconstructed reliably, shortened matches, and chases that do not reach 36 legal balls in the first six overs. Exclusions are for a well-defined prediction time and target, not chart appearance. The inference is observational and predictive, not causal. No runs, wickets, or matches will be removed because they look extreme.

## Keim-style workflow, established before implementation

1. **Original data:** A1 `matches.csv` and `deliveries.csv`.
2. **Transform/preprocess:** validate keys and types; aggregate first-innings target and six-over chase state; apply the stated eligibility rules; emit one row per match.
3. **Iteration 1 visualization:** show score/wicket distributions and chase-success rates across first-iteration state groups.
4. **Iteration 1 analysis:** descriptive uncertainty estimates, unsupervised K-means on standardized raw state, and temporal-holdout logistic regression using six-over runs and wickets only.
5. **Inference:** runs and wickets alone do not encode the size of the target still required; success varies sharply with the implied required rate.
6. **Feedback loop transformation:** add `runs_remaining`, `legal_balls_remaining`, and derived `required_run_rate` at the six-over observation point. This changes the representation/model inputs while preserving the original match and outcome rows.
7. **Iteration 2 visualization:** show chase success against required rate and cluster profiles in pressure-aware space; compare the target-aware model to iteration 1 on the same chronological test matches.
8. **Final inference/knowledge:** report whether the transformation clarifies the outcome gradient and improves held-out prediction; state limits and alternative explanations.

The implemented stages will map to `src/data_loading.py`, `src/preprocessing.py`, `src/analysis.py`, `src/modeling.py`, `src/transformation.py`, `src/visualization.py`, and `run_all.py`. The diagram will only include these actual stages and will unroll the second iteration with the feedback edge labeled verbatim.

## Method and visualization selection

| Method | Inputs | Purpose and expected output | Why appropriate | Visualization / supported inference |
|---|---|---|---|---|
| Descriptive and group-rate analysis | Six-over state, target pressure, chase result | Counts, distributions, success rates, uncertainty intervals | Transparent summary of a binary outcome and a small state table | Rate-by-pressure plot shows how outcome prevalence changes with match context |
| Bootstrap interval for low/high pressure rate difference | Binary chase outcome in first/last required-rate quartile | Difference in rates and percentile 95% interval | Does not require a normal outcome distribution; resampling is match-level | Interval plot conveys magnitude and uncertainty, not only a p-value |
| K-means, k=4, fixed seed | Standardized six-over runs and wickets; then add required rate in iteration 2 | Cluster assignments and centers | Groups common match states without treating labels as real-world categories | Cluster/profile plot interprets centers as algorithmic summaries, not natural match types |
| Majority baseline and logistic regression | Iteration 1: six-over runs and wickets. Iteration 2: same inputs plus required rate. | Binary probability and fixed-holdout accuracy, precision, recall, F1, ROC-AUC, confusion matrix | Binary target is recorded by the match table; logistic model is interpretable. The test set is later by date, preventing future-to-past evaluation. | Model comparison supports only held-out predictive comparison; coefficients/probabilities are not causal effects |
| Iteration 1 scatter/summary | Six-over runs, wickets lost, chase success | Initial visual pattern | Directly displays observed match states and outcomes | Reveals whether run/wicket state alone mixes wins and losses |
| Iteration 2 rate/profile view | Required rate, success, cluster summaries | Reframed state-space structure | Required rate is known at the chosen prediction point and communicates target pressure | Reveals outcome gradient and how pressure changes state grouping |

No arbitrary minimum-sample threshold is planned. All charts will state their sample size. Missing match outcomes or ambiguous targets are excluded through the explicit eligibility rules. Any model preprocessing parameters will be fit on training data only. The random seed and temporal cutoff will be fixed and recorded.

### Visualization plan

| Figure | Question and variables | Chart and encodings | What to look for / expected inference | Connection |
|---|---|---|---|---|
| Iteration 1 state outcome heatmap | Do six-over runs and wickets separate outcomes? Runs quartile × wickets lost band; color = chase-success share; labels = share and match count. | Heatmap, sequential color for a proportion. | Look for cells with different outcome rates and sparse combinations; test whether raw state alone provides a useful account. | Leads to iteration-one inference that a target-relative feature may be missing. |
| Iteration 1 cluster projection | What raw chase states recur? Runs × wickets; color = K-means cluster; X = center. | Scatter plot, color encodes algorithmic group. | Look for common low/high scoring and wicket-loss profiles, not natural categories. | Shows how unsupervised grouping summarizes the first state space. |
| Iteration 2 pressure outcome bars | Does required run rate change observed chase success? Required-rate quartile × success share; color = increasing pressure; error bars = Wilson 95% interval; labels = n. | Bar and interval plot for a binary rate across ordered groups. | Look for a monotonic or non-monotonic gradient and uncertainty; actual Q1/Q4 contrast is quantified in generated output. | Directly visualizes the feedback transformation's central feature. |
| Iteration 2 cluster projection | How does adding target context change state groups? Runs × required rate; color = transformed K-means cluster; X = center. | Scatter plot with center markers. | Look for pressure variation among similar raw runs and shifted cluster profiles. | Checks how the transformed representation alters unsupervised structure. |
| Model comparison | Does required rate add held-out prediction information? Model name × accuracy/F1/ROC-AUC; color = metric. | Grouped bars on identical later-date test matches. | Compare against majority baseline and iteration-one model; avoid treating one metric as proof of causality or future generalization. | Quantitatively compares the two workflow iterations. |

## Known risks and checks

- A1 delivery data has nulls in event-specific fields and exact duplicate-looking rows. Nulls and repeated events must be interpreted against the schema; no blind deduplication is planned. The natural key `(match_id, innings, over, ball)` may be non-unique because deliveries can include extras or be recorded with repeated ball indices; key checks will report this rather than treating it as proof of corruption.
- First-innings total includes all recorded runs and extras; target is total plus one. D/L matches are excluded because a revised target is not represented by the simple first-innings total.
- Model performance can vary with rule eras, teams, venue, and season. The main model deliberately uses a short interpretable feature set; it is not intended as a production prediction system.
- The A1 team-alias normalization and earlier figures are inherited context, not automatically applied to the selected chase-state model.
- Team contribution statement remains a placeholder for the group to complete honestly.
