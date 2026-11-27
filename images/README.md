# Image index

| Figure | File | Title / question | Main inference | Workflow iteration |
|---:|---|---|---|---|
| 1 | `workflow_diagram.png` | How does the implementation unroll the visual analytics workflow? | Iteration-one inference triggers the required-rate transformation; iteration two has new analysis and visualization stages. | Both |
| 2 | `iteration1_state_outcomes.png` | Do six-over runs and wickets alone separate chase outcomes? | Shows outcome rates across raw-state bands before target pressure is encoded. | 1 |
| 3 | `iteration1_clusters.png` | What raw six-over states recur in the data? | K-means centers summarize groupings in runs/wickets; cluster labels are algorithmic. | 1 |
| 4 | `iteration2_pressure_outcomes.png` | How does required run rate relate to chase success? | Shows the observed win-rate gradient across pressure quartiles with Wilson intervals. | 2 |
| 5 | `iteration2_clusters.png` | How does target context change the state-space grouping? | Adds required rate to the clustering inputs while retaining the same match rows. | 2 |
| 6 | `model_comparison.png` | Does target pressure add held-out predictive information? | Compares baseline, raw-state and pressure-aware models on later dates. | 1 and 2 |

All PNGs are generated at 240 dpi by `run_all.py`. Figure values and counts come from `outputs/results/results.json` and its CSVs.
