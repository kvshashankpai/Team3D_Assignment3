"""Generate the LaTeX report from actual pipeline result files."""

from __future__ import annotations

from pathlib import Path
import json
import shutil


def _pct(value: float) -> str:
    return f"{100 * value:.1f}" + r"\%"


def _num(value: float, places: int = 3) -> str:
    return f"{value:.{places}f}"


def _latex_escape(value: object) -> str:
    text = str(value)
    for before, after in [("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")]:
        text = text.replace(before, after)
    return text


def generate_report(root: Path, results: dict[str, object] | None = None) -> None:
    report_dir = root / "report"
    appendix_dir = report_dir / "appendices"
    appendix_dir.mkdir(parents=True, exist_ok=True)
    source_appendix = root.parent / "Assignment1" / "new_data" / "IPL_Data_Visualization_Project_Report.pdf"
    target_appendix = appendix_dir / "A1_Report.pdf"
    if not target_appendix.exists():
        if not source_appendix.is_file():
            raise FileNotFoundError(f"A1 report required for appendix is missing: {source_appendix}")
        shutil.copy2(source_appendix, target_appendix)
    if results is None:
        results = json.loads((root / "outputs" / "results" / "results.json").read_text(encoding="utf-8"))

    summary = results["summary"]
    audit = results["eligibility_audit"]
    models = results["models"]["models"]
    split = results["models"]["split"]
    q1 = summary["pressure_q1_success_rate"]
    q4 = summary["pressure_q4_success_rate"]
    diff_ci = summary["pressure_difference_ci_95_season_block"]
    i1 = models["iteration1_raw_state"]
    i2 = models["iteration2_target_pressure"]
    base = models["majority_baseline_probability"]

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[margin=0.85in]{{geometry}}
\usepackage[T1]{{fontenc}}
\usepackage{{lmodern}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{pdfpages}}
\usepackage{{caption}}
\usepackage{{float}}
\usepackage{{microtype}}
\hypersetup{{colorlinks=true,linkcolor=blue!55!black,urlcolor=blue!55!black,citecolor=blue!55!black}}
\graphicspath{{{{../images/}}}}
\setlength{{\parskip}}{{0.45em}}
\setlength{{\parindent}}{{0pt}}
\title{{\textbf{{Reading Chase Pressure at the Six-Over Mark}}\\[0.3em]
\large DAS732 Programming Assignment 3: Visual Analytics Workflow}}
\author{{Team 3\\\small IIIT Bangalore, Term 1 (2026--27)\\[0.5em]
\small Team members, listed in A2 disclosures (confirm A3 roster):\\
K V Shashank Pai (BT2024250); Adithya Kommuri (BT2024246);\\
Nishanth Karamsetty (BT2024094)}}
\date{{November 2026}}
\begin{{document}}
\maketitle

\begin{{abstract}}
This project studies whether the score and wickets after six completed overs explain eventual IPL chase success, and whether the target-relative required run rate adds useful context. From {summary['n_matches']:,} eligible match states, we compare a raw-state view and model with a target-aware second iteration. A season-block bootstrap estimates the difference in win rates between the lowest and highest required-rate quartiles as {_pct(summary['pressure_low_high_rate_difference'])} (95\% interval {_pct(diff_ci[0])} to {_pct(diff_ci[1])}). On a later-date holdout, the raw-state logistic model has ROC--AUC {_num(i1['roc_auc'])} and the target-aware model has ROC--AUC {_num(i2['roc_auc'])}. The project treats these as descriptive and predictive patterns, not causal effects.
\end{{abstract}}

\section{{Introduction and problem statement}}
The A1 IPL story explored scoring trends, team and player profiles, bowling, toss decisions, and venues. This A3 analysis narrows the focus to one moment: the end of six legal overs in a second innings. The research question is: \textit{{How do runs and wickets at this checkpoint relate to chase success, and what additional information is contained in the required scoring rate implied by the first-innings target?}}

This question is useful for studying how raw progress depends on the task still remaining. It does not assert that pressure causes a team to win or lose. The main contribution beyond A1 is a reproducible match-state table, unsupervised state grouping, a leakage-aware supervised model, and an inference-triggered transformation followed by a second visual iteration.

\section{{Dataset and preparation}}
The primary data are the A1 IPL match and delivery tables: 1,243 matches and 295,732 ball-level rows over 19 season labels from 2008-04-18 to 2026-05-31. The A1 report and its 15 visualizations are included in Appendix A for context; their old figures and conclusions are not presented as new A3 analyses. A2's gridMET meteorological data were inspected but not added because they do not materially support an IPL chase question.

The unit of analysis is one match's second-innings state after 36 legal balls in overs 0--5. Target equals first-innings total runs plus one. Chase success is whether the second-innings batting team matches the official winner. The pipeline retains all source delivery rows and excludes super-over events, ties, no-results, D/L matches, matches scheduled for fewer than seven overs, and innings with fewer than 36 legal balls in the first six overs. The final table contains {audit['eligible_states']:,} observations ({audit['successful_chases']:,} successful chases and {audit['unsuccessful_chases']:,} unsuccessful chases). The filtering does not remove outliers for visual convenience.

\section{{Visual analytics workflow}}
The workflow follows Keim et al.'s visual analytics process: data preparation, visualization and analysis interact to support interpretation. Figure~\ref{{fig:workflow}} unrolls the two iterations. The first iteration displays six-over runs and wickets, analyzes their outcome patterns, and identifies omitted target context. That quantified inference triggers the feedback transformation. The second iteration visualizes required rate and target-aware clusters, with a same-test-set model comparison.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.94\linewidth]{{workflow_diagram.png}}
\caption{{Unrolled visual analytics workflow. Every implementation stage maps to a source module or the pipeline orchestrator. The labeled feedback edge connects the iteration-one inference to the pressure-feature transformation.}}
\label{{fig:workflow}}
\end{{figure}}

\section{{Methods and model safeguards}}
\begin{{table}}[H]
\centering\small
\begin{{tabular}}{{p{{0.17\linewidth}}p{{0.24\linewidth}}p{{0.25\linewidth}}p{{0.25\linewidth}}}}
\toprule
Method & Inputs & Purpose and output & Rationale / visual encoding \\
\midrule
Descriptive rates and Wilson intervals & Six-over state, outcome, pressure quartile & Match counts and outcome proportions & Direct summaries for a binary outcome; rate plots include sample sizes and intervals. \\
Season-block bootstrap & Match-level Q1 and Q4 outcomes & 95\% interval for the low-minus-high rate difference & Resamples whole seasons to partially account for within-season dependence. \\
K-means, $k=4$ & Standardized runs and wickets; iteration 2 also includes required rate & State assignments, centers, inertia, silhouette & Unsupervised summary of common states; labels are algorithmic, not real-world categories. \\
Logistic regression & Iteration 1: runs, wickets; iteration 2 adds required rate & Chase probability on later-date matches & Binary label is observed; chronological evaluation and train-only scaling reduce leakage. \\
\bottomrule
\end{{tabular}}
\caption{{Methods used and the outputs they support.}}
\label{{tab:methods}}
\end{{table}}

For supervised prediction, the target is \texttt{{chase\_success}}. The majority-probability baseline and both logistic models use the same chronological holdout. The cutoff is {split['cutoff_date_inclusive_for_test']}; the training period ends {split['train_date_max']}, and testing begins {split['test_date_min']}. Standardization parameters are fit only on training rows. The 0.5 threshold is fixed for accuracy, precision, recall, and F1; ROC--AUC and Brier score are computed from probabilities. No post-checkpoint delivery features enter either model.

\section{{Iteration 1: raw chase state}}
Figure~\ref{{fig:i1state}} compares observed chase-success rates across six-over run quartiles and wicket-loss bands. It answers whether raw progress separates outcomes while leaving the first-innings target out of the display. Figure~\ref{{fig:i1cluster}} shows the four K-means groups built on standardized runs and wickets. The clusters summarize recurring locations in state space; they do not imply four natural kinds of chase.

\begin{{figure}}[H]\centering
\includegraphics[width=0.83\linewidth]{{iteration1_state_outcomes.png}}
\caption{{Iteration 1: chase-success share by powerplay run quartile and wickets lost. Cell labels show the observed share and match count. The matrix reveals how the two raw state variables relate to outcomes before target context is encoded.}}
\label{{fig:i1state}}\end{{figure}}

\begin{{figure}}[H]\centering
\includegraphics[width=0.82\linewidth]{{iteration1_clusters.png}}
\caption{{Iteration 1 K-means projection. Points are match states; X markers are cluster centers. Cluster identifiers are display indices only.}}
\label{{fig:i1cluster}}\end{{figure}}

\subsection{{Iteration-one inference and feedback trigger}}
The initial analysis suggested that score and wickets alone omit how much scoring remains necessary. The first-innings target is available before the chase, so required run rate at the checkpoint can be derived without using future deliveries. The lowest pressure quartile's success rate is {_pct(q1)} and the highest's is {_pct(q4)}, a Q1--Q4 difference of {_pct(summary['pressure_low_high_rate_difference'])} (95\% season-block interval {_pct(diff_ci[0])} to {_pct(diff_ci[1])}). This quantitative contrast justifies adding the number of runs remaining and required run rate to the state representation. It does not imply pressure caused the outcome.

\section{{Feedback transformation}}
The transformation adds \texttt{{runs\_remaining = target - runs\_after\_six}} and \texttt{{required\_run\_rate = 6 * runs\_remaining / legal\_balls\_remaining}}. Each row remains one match and keeps the same target, outcome, and raw six-over runs/wickets. No match is dropped by the transformation. The schedule's listed overs determine remaining legal balls. This changes the question from \emph{{how much has the chase scored?}} to \emph{{how much must it score per over from here?}}.

\section{{Iteration 2: target-aware view}}
Figure~\ref{{fig:i2pressure}} visualizes chase success by required-rate quartile with Wilson intervals. Figure~\ref{{fig:i2cluster}} repeats K-means after adding required rate, changing the clustering input from two raw state dimensions to a target-aware three-dimensional state. Figure~\ref{{fig:models}} compares the majority baseline and both logistic models on identical later-date matches.

\begin{{figure}}[H]\centering
\includegraphics[width=0.83\linewidth]{{iteration2_pressure_outcomes.png}}
\caption{{Iteration 2: observed chase success by required-rate quartile. Error bars are Wilson 95\% intervals; labels report sample sizes. The bootstrap interval in the text resamples season blocks.}}
\label{{fig:i2pressure}}\end{{figure}}

\begin{{figure}}[H]\centering
\includegraphics[width=0.82\linewidth]{{iteration2_clusters.png}}
\caption{{Iteration 2 K-means projection after required run rate is added. The match rows are unchanged; this view displays how target context alters the represented state space.}}
\label{{fig:i2cluster}}\end{{figure}}

\begin{{figure}}[H]\centering
\includegraphics[width=0.86\linewidth]{{model_comparison.png}}
\caption{{Majority baseline and logistic models evaluated on the same later-date holdout. Metrics are accuracy, F1, and ROC--AUC; higher is better.}}
\label{{fig:models}}\end{{figure}}

On the chronological holdout, the raw-state model has accuracy {_num(i1['accuracy'])}, F1 {_num(i1['f1'])}, and ROC--AUC {_num(i1['roc_auc'])}; adding required rate gives accuracy {_num(i2['accuracy'])}, F1 {_num(i2['f1'])}, and ROC--AUC {_num(i2['roc_auc'])}. The majority-probability baseline has accuracy {_num(base['accuracy'])} and ROC--AUC {_num(base['roc_auc'])}. These results show whether the transformation improves prediction in this split; the Q1--Q4 descriptive gradient remains the main finding.

\section{{Final findings}}
\begin{{enumerate}}
\item Target-relative pressure distinguishes chase states that look similar when described only by six-over runs and wickets: the observed success share changes from {_pct(q1)} in the lowest required-rate quartile to {_pct(q4)} in the highest.
\item The transformed representation makes this relationship visible directly and lets the second logistic model test whether required rate adds held-out predictive information.
\item Clustering supplies a second view of state structure, but its labels are algorithm-dependent. It is not used to claim that cricket teams or chases fall into objectively discrete types.
\end{{enumerate}}

\section{{Limitations and alternative explanations}}
The data are observational. Team strength, opponent, toss, venue, rules, season, weather, and match conditions may influence both the six-over state and the outcome. A single chronological test period may differ from future seasons. The source contains repeated delivery rows and repeated over/ball keys; because identical wides may be distinct events and the available schema cannot disambiguate them, no blind deduplication was performed. Excluding D/L, short, tied, no-result, and early-ending chases narrows the population. The bootstrap uses only 19 season blocks. A future analysis could use over-by-over trajectories, season/team-adjusted models, calibration analysis, or a different target-normalized rate, provided that each feature is available at the prediction time and the test split remains valid.

\section{{Conclusion}}
The visual analytics workflow starts with raw six-over chase state, identifies a measurable omission, encodes that omission as required run rate, and returns to the data in a second visual and modeling iteration. The target-aware view answers a more useful question about progress relative to the task remaining. It provides an interpretable, reproducible story while keeping prediction separate from causal explanation.

\section{{Team contribution statement}}
\textbf{{Placeholder -- complete with the group's agreed, truthful contributions before submission.}} The A2 disclosure files list K V Shashank Pai, Adithya Kommuri, and Nishanth Karamsetty; confirm that this remains the A3 group. Add each member's actual A3 contribution. The technical workflow was implemented by the requesting student; confirm the name and describe only work that was actually performed.

\section*{{References}}
\begin{{thebibliography}}{{9}}
\bibitem{{keim2008}} D. A. Keim, J. Kohlhammer, G. Ellis, and F. Mansmann, editors, \emph{{Mastering the Information Age: Solving Problems with Visual Analytics}}. Eurographics Association, 2010. See also D. A. Keim et al., ``Visual Analytics: Definition, Process, and Challenges,'' in \emph{{Information Visualization}}, 2008.
\bibitem{{macqueen1967}} J. MacQueen, ``Some methods for classification and analysis of multivariate observations,'' in \emph{{Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability}}, vol. 1, pp. 281--297, 1967.
\bibitem{{hosmer2013}} D. W. Hosmer, S. Lemeshow, and R. X. Sturdivant, \emph{{Applied Logistic Regression}}, 3rd ed. Wiley, 2013.
\bibitem{{a3prompt}} International Institute of Information Technology Bangalore, ``DAS732 Programming Assignment 3: Visual Analytics Workflow,'' Term 1 (2026--27), course handout.
\bibitem{{a1report}} DAS732 A1 IPL Analytics Project, ``IPL Cricket Data Story: A 15-Visualization Analysis,'' student report included in Appendix A.
\end{{thebibliography}}

\appendix
\section{{A1 report (completeness appendix)}}
The following pages reproduce the A1 report. As specified by the A3 assignment, this appendix is included for completeness and is not assessed as part of A3.
\includepdf[pages=-]{{appendices/A1_Report.pdf}}
\end{{document}}
"""
    (report_dir / "main.tex").write_text(tex, encoding="utf-8")
    (report_dir / "README.md").write_text(
        "# LaTeX report project\n\n"
        "Compile `main.tex` with a LaTeX engine that provides `pdfpages`, `graphicx`, `booktabs`, and `lmodern`. "
        "Figures live in `../images/`; the unchanged A1 report appendix is `appendices/A1_Report.pdf`. "
        "All result values in `main.tex` are generated from `outputs/results/results.json` by `run_all.py`.\n",
        encoding="utf-8",
    )
    (report_dir / "references.bib").write_text(
        """@book{keim2010,
  editor={Keim, Daniel A. and Kohlhammer, Jörn and Ellis, Geoff and Mansmann, Florian},
  title={Mastering the Information Age: Solving Problems with Visual Analytics},
  publisher={Eurographics Association},
  year={2010}
}

@inproceedings{macqueen1967,
  author={MacQueen, J.},
  title={Some methods for classification and analysis of multivariate observations},
  booktitle={Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability},
  volume={1}, pages={281--297}, year={1967}
}

@book{hosmer2013,
  author={Hosmer, David W. and Lemeshow, Stanley and Sturdivant, Rodney X.},
  title={Applied Logistic Regression}, edition={3}, publisher={Wiley}, year={2013}
}
""",
        encoding="utf-8",
    )
