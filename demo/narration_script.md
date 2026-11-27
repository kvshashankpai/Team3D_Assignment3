# Video Demo Narration Script

## Dataset and question

We use the IPL match and ball-by-ball files from Assignment 1. Each row in our analysis represents a second-innings chase after six completed legal overs. We ask whether runs and wickets at that point describe the chance of completing the chase, and whether the target still required adds important context.

## First iteration

This heatmap compares observed chase success across powerplay run quartiles and wicket-loss groups. The scatter summarizes the raw-state clusters. K-means uses standardized runs and wickets; its numbered groups are algorithmic summaries, not real cricket categories. The first model uses only these two checkpoint features. The model is compared with a majority baseline on later match dates, so future matches do not train predictions for earlier ones.

## Inference and feedback loop

The first iteration leaves out the size of the target. A score of 45 after six overs may be comfortable or difficult depending on the first innings. In these data, success is 86.8 percent in the lowest required-rate quartile and 16.1 percent in the highest, a difference of 70.7 percentage points. This supports a specific transformation: derive runs remaining and required runs per over from the first-innings target, current score, and legal balls remaining. All are known at the end of six overs.

## Second iteration and conclusion

The second visualization plots observed chase success by required-rate quartile with confidence intervals. We also repeat clustering with required rate included and compare a target-aware logistic model on exactly the same later-date matches. On this holdout, ROC-AUC rises from 0.729 to 0.890 and accuracy from 0.677 to 0.777. The comparison is predictive, not causal. Our conclusion is that target-relative pressure makes the match state easier to interpret and adds useful held-out information in this split. The analysis excludes D/L matches, ties, no-results, short matches, and chases that end before the checkpoint, and the source delivery table contains repeated event rows that we preserve rather than deduplicate without proof.

## Recording cue

Insert the generated metric values from `outputs/results/results.json` when narrating the model comparison. Finish by opening the workflow diagram and showing the labeled feedback edge from the quantified inference to the transformation.
