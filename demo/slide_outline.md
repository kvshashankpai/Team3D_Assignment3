# Video Demo Slide Outline

Target duration: about 4 minutes. Keep the narration focused on why each stage follows from the previous one. Use the figures in `../images/` and show `run_all.py` only briefly.

| Segment | Suggested time | Visual / file | What to explain |
|---|---:|---|---|
| 1. Dataset and question | 0:00–0:35 | `../images/workflow_diagram.png`; `../outputs/results/inventory.md` | A1 IPL match and delivery tables; one row per eligible chase at the end of six overs; what can be predicted at that moment. |
| 2. Iteration 1 | 0:35–1:15 | `../images/iteration1_state_outcomes.png`; `../images/iteration1_clusters.png` | How raw six-over runs and wickets relate to chase outcomes and how K-means summarizes state locations. |
| 3. Statistical and ML methods | 1:15–1:50 | `../images/model_comparison.png` | Explain the majority baseline, chronological split, logistic regression, and why no future deliveries enter the features. |
| 4. Inference and feedback loop | 1:50–2:35 | `../images/iteration2_pressure_outcomes.png`; `src/transformation.py` | Explain the measured low/high pressure gradient, the required-rate formula, and why it is known at the checkpoint. |
| 5. Iteration 2 and final story | 2:35–3:25 | `../images/iteration2_clusters.png`; `../images/model_comparison.png` | Show the target-aware clustering and held-out model comparison; state honestly if predictive performance changes little or worsens. |
| 6. Reproducibility and limits | 3:25–4:00 | `run_all.py`; `outputs/results/validation.md` | Show the one-command rerun, the source-data prerequisite, observational limitations, and the contribution placeholder. |

Before recording, replace any figures with the final pipeline outputs and verify names against `images/README.md`. The team must make and submit the actual video; this package is a recording guide, not a video file.
