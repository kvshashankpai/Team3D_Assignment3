# Viva Preparation: IPL Chase Pressure

## Two-to-three-minute spoken summary

Our question is whether the score and wickets after six legal overs explain whether an IPL team completes a chase, and whether the first-innings target adds important context. We use the A1 match and delivery tables. A match-level row is created only when the second innings reaches 36 legal balls in overs zero through five and the match has a standard, resolved, non-D/L result. This leaves 1,194 chase states: 649 successful and 545 unsuccessful.

Iteration one visualizes chase success over raw six-over runs and wicket-loss bands. We also cluster standardized runs and wickets using K-means and fit logistic regression using only those two state features. This gives us a clear baseline and respects the prediction time: no later deliveries enter the features.

The first-innings target is known before the chase, but raw runs do not say how much scoring remains necessary. We quantify that missing context: success is 86.8 percent in the lowest required-rate quartile and 16.1 percent in the highest. The difference is 70.7 percentage points, with a 95 percent season-block bootstrap interval from 65.0 to 76.3 points. That finding triggers the feedback transformation. We derive runs remaining and required runs per over from the target, current score, and remaining legal balls; we do not remove or change match rows.

Iteration two visualizes the pressure gradient, reclusters the target-aware state, and adds required rate to logistic regression. On the same later-date test matches, ROC-AUC rises from 0.727 to 0.890, accuracy from 0.676 to 0.776, and Brier score improves from 0.210 to 0.148. This is evidence for predictive value in this time split, not a causal effect or a guarantee about future seasons. The Q1/Q4 gradient is the main descriptive finding. K-means labels are algorithmic groupings, and the second clustering has a lower silhouette score, so we do not call the transformed clusters objectively better.

## Thirty-five likely questions

### Dataset and research question

1. **What data did you use?** The A1 IPL `matches.csv` and `deliveries.csv` tables: 1,243 matches and 295,732 delivery rows. The pipeline audits the other A1 roster, player, and official tables as well.
2. **What is the date and season coverage?** Matches run from 18 April 2008 to 31 May 2026 and span 19 season labels.
3. **What is the unit of analysis?** One eligible match's second-innings state after six completed legal overs.
4. **Why study the six-over checkpoint?** It is a meaningful early decision point with enough deliveries observed to describe progress while leaving most of a chase ahead.
5. **What is your research question?** How do six-over runs and wickets relate to eventual chase success, and does required run rate add information because the target differs between matches?
6. **How is this different from A1?** A1 primarily used visual exploration of league, team, batting, bowling, and venue patterns. A3 adds a match-state prediction task, clustering, statistical uncertainty, and a quantified feedback loop.
7. **Why did you not merge the A2 climate dataset?** It is a separate spatial-temporal dataset and does not materially answer an IPL chase question.

### Workflow and feedback loop

8. **How does the workflow follow Keim's visual analytics diamond?** It cycles through data preparation, visualization, analysis, and interpretation; the diagram unrolls the second pass so the feedback transformation is explicit.
9. **What is the triggering inference?** The lowest and highest required-rate quartiles have 86.8% and 16.1% chase success, a 70.7 percentage-point difference; the season-block 95% interval is 65.0–76.3 points.
10. **Why is that a feedback loop rather than another chart?** An inference from iteration one changes the data representation and model inputs, then iteration two re-visualizes and re-evaluates that transformed state.
11. **What exactly changes in the transformation?** It adds `runs_remaining = target_runs - runs_after_six` and `required_run_rate = 6 * runs_remaining / legal_balls_remaining`. The same 1,194 matches and original state fields remain.
12. **Why use required run rate?** It expresses target-relative work remaining per over and is available at the checkpoint without future deliveries.
13. **What if the transformation were removed?** Iteration two would lose target context; the pressure gradient could not be represented as a checkpoint feature, and the model would remain the raw-state model.
14. **What alternative transformation could you try?** Target-relative run rate compared with current rate, or an over-by-over trajectory. Each would need a new timing/leakage check and a reasoned comparison.

### Preprocessing and data quality

15. **How did you define a legal ball?** A delivery row with zero wides and zero no-balls. Extras still contribute to total runs.
16. **How did you calculate the target?** The first innings' recorded `total_runs` summed across regular deliveries, plus one.
17. **Why exclude D/L matches?** The simple first-innings sum does not capture the revised target, so treating it as the target would mislabel pressure.
18. **Why exclude ties and no-results?** The binary outcome is ambiguous for a tie and absent for a no-result; the analysis needs a resolved official winner.
19. **Why exclude chases ending before six overs?** There is no state after a completed six-over checkpoint, so they are not part of this prediction-time population.
20. **Did you remove duplicate rows?** No. There are 470 exact repeated delivery rows and repeated `(match_id, innings, over, ball)` keys. Identical wides can be separate events; the schema alone cannot prove duplication, so the pipeline retains and flags them.
21. **Did you trim outliers?** No. No observations were removed to improve chart appearance. Eligibility rules establish a valid checkpoint and outcome.
22. **What are the main exclusions and final count?** From 1,243 matches, the final analysis uses 1,194: standard, normal, resolved non-D/L matches with a complete six-over state.

### Statistical and machine-learning methods

23. **What statistical analysis did you use?** Descriptive rates by pressure quartile, Wilson 95% intervals, and a 2,000-replicate season-block bootstrap for the Q1–Q4 success-rate difference.
24. **Why no p-value?** The main question is a descriptive group contrast; the report presents effect size and uncertainty rather than a p-value alone. The bootstrap does not assume normally distributed binary outcomes.
25. **What are the bootstrap assumptions and limitations?** Season blocks are resampled as units to account partly for within-season dependence. There are only 19 seasons, and seasons are not guaranteed to be exchangeable.
26. **What is the supervised target?** `chase_success`: whether the second-innings batting side is the official match winner.
27. **Which model did you use?** L2-regularized binary logistic regression, trained by batch gradient descent with learning rate 0.1, alpha 0.02, 0.5 threshold, and fixed stopping tolerance.
28. **What is the baseline?** A constant probability equal to the training-set success proportion. At the fixed 0.5 threshold it predicts the majority class for every test case.
29. **How did you split the data?** Chronologically by distinct date anchors: train through 17 May 2023 (974 rows), test from 18 May 2023 through 31 May 2026 (220 rows).
30. **How did you avoid leakage?** Winner is used only for the label. Features use only the first six overs and pre-chase target. Means and standard deviations are fit on training data only, and the test dates are later than training dates. The match date is a split variable, not a model predictor.
31. **What were the actual test results?** Raw state: accuracy 0.677, F1 0.736, ROC-AUC 0.729, Brier 0.209. Target-aware: 0.777, 0.774, 0.890, and 0.148. Majority-probability baseline ROC-AUC is 0.500 and Brier 0.248.
32. **Why report more than accuracy?** Outcome imbalance and a majority predictor can make accuracy misleading. F1, ROC-AUC, Brier score, precision, and recall show thresholded and probability-ranking behavior.

### Clustering and visualization

33. **Why K-means?** Runs, wickets, and required rate are numeric state variables; scaling and Euclidean distance provide an understandable way to summarize recurring states.
34. **Why four clusters?** Four is a fixed, interpretable display choice for comparing a small number of profiles. It is not asserted as the true number of cricket categories; silhouette is reported as a diagnostic.
35. **What do cluster labels mean?** They are arbitrary algorithmic group identifiers. Iteration-one silhouette is 0.375 and iteration-two silhouette is 0.246; the target-aware clusters are not objectively more compact by this measure.
36. **Why use a heatmap first?** It shows two raw state dimensions and outcome rate together while annotating sample size, making sparse combinations visible.
37. **Why use bars with intervals for pressure?** Required rate is divided into ordered groups; bars compare outcome proportions and intervals communicate uncertainty.
38. **Why a scatter for clusters?** It shows individual match states, overlap, and the cluster centers in interpretable units.

### Interpretation and limitations

39. **Can you say required rate causes chase failure?** No. This is observational. Team skill, opposition, venue, rules, toss, and match conditions can affect both state and outcome.
40. **Does the model prove generalization?** No. It improves on a later-date holdout in this dataset; a different future period or changing rules may yield different performance.
41. **Why does the target-aware model have fewer false positives but more false negatives?** On this split it is more conservative: 12 false positives and 37 false negatives versus 49 and 22 for raw state. A threshold or cost-sensitive decision would change that tradeoff.
42. **What is the largest data limitation?** Repeated delivery records cannot be resolved confidently from the available event columns; the analysis retains them and reports that limitation.
43. **What happens if you change cluster count or seed?** Membership and display profiles can shift. The seed is fixed for reproducibility; a broader sensitivity analysis across k and random starts is future work.
44. **What would you add next?** Season- and team-aware calibration, an over-by-over trajectory, and a sensitivity analysis of event duplicates and cluster count, while preserving temporal evaluation.
45. **What should the contribution section say?** The group must enter its agreed, truthful contributions. The report intentionally leaves this as a placeholder rather than fabricating a split.

## Per-module walkthrough

- `run_all.py`: the orchestrator. Reads tables, creates iteration-one states, transforms them, runs analyses/models, writes figures and audit outputs, then generates the report.
- `src/data_loading.py`: resolves `IPL_DATA_DIR` or the sibling A1 folder, reads five tables, checks key integrity and table quality.
- `src/preprocessing.py`: separates regular innings, sums first-innings target, aggregates overs 0–5, verifies the completed checkpoint, and labels chase success.
- `src/analysis.py`: computes quartile tables, Wilson intervals, heatmap input, and season-block bootstrap.
- `src/modeling.py`: implements seeded K-means and L2 logistic regression, chronological holdout, baseline, and evaluation metrics.
- `src/transformation.py`: derives runs remaining and required rate; it does not change the row set.
- `src/visualization.py`: creates the five analytical figures with labeled encodings at 240 dpi.
- `src/workflow_render.py`: draws the workflow PNG from the same staged design described in `report/workflow.mmd`.
- `src/reporting.py`: copies the A1 report to the appendix if missing and generates `report/main.tex` from actual `results.json` values.

## Important parameters

- Six-over checkpoint: 36 legal balls; delivery overs are indexed 0 through 5.
- Required rate: remaining runs × 6 / remaining legal balls; the scheduled overs field provides total legal balls.
- Bootstrap: 2,000 season-block replicates, seed 732, percentile 95% interval.
- K-means: k=4, standardized input variables, 10 initializations, seed 732; silhouette and inertia are reported.
- Logistic regression: L2 alpha 0.02, batch gradient descent, learning rate 0.1, 0.5 decision threshold; scaling fitted on train only.
- Holdout: later date anchors from 18 May 2023; 974 training rows and 220 test rows. The cutoff and date ranges are in `outputs/results/results.json`.

## Before the viva

Rerun `python3 run_all.py`, read `PLAN.md`, `outputs/results/data_quality.md`, `outputs/results/results.json`, `outputs/results/validation.md`, and `report/main.tex`. Review the report's contribution placeholder and complete it truthfully with the group. The video recording remains a team deliverable; use `demo/slide_outline.md` and `demo/narration_script.md` to prepare it.
