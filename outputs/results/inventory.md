# Existing Project Inventory

## Workspace status

The A3 project directory initially contained only `DAS732_T1-26-27_A3.pdf`; there was no pre-existing A3 source code, report, or generated output to overwrite. The neighboring `Assignment1` and `Assignment2` directories were inspected as the available course work.

## Assignment 1: IPL

There are two distinct A1 data snapshots. `../Assignment1/data/` contains `matches.csv` (1,158 × 25), `deliveries.csv` (134,190 × 18), `players.csv` (580 × 12), and `seasons.csv` (18 × 14), with `M0001`-style match IDs and a different schema. Its match IDs do not overlap the later source below. The analysis uses `../Assignment1/new_data/`, whose counts match the supplied A1 report and Tableau-era story materials; the two snapshots are not merged.

| Asset | Location | Observed structure / use |
|---|---|---|
| Matches | `../Assignment1/new_data/matches.csv` | 1,243 rows × 21 columns; 2008-04-18 through 2026-05-31; 19 season labels. Match metadata and winner/target context. |
| Deliveries | `../Assignment1/new_data/deliveries.csv` | 295,732 rows × 22 columns; ball-level runs, extras, wickets, teams, innings, over, and super-over marker. |
| Match players | `../Assignment1/new_data/match_players.csv` | 27,909 rows × 4 columns; match roster relationships. |
| Players | `../Assignment1/new_data/players.csv` | 811 rows × 2 columns; player ID/name lookup. |
| Officials | `../Assignment1/new_data/officials.csv` | 6,187 rows × 3 columns; official assignments. |
| Tableau workbook | `../Assignment1/new_data/IPL_Visualizations.twb` | Existing multi-sheet Tableau visual exploration. Its data source declares deliveries and matches, among other A1 tables. |
| A1 report | `../Assignment1/new_data/IPL_Data_Visualization_Project_Report.pdf` and `.docx` | 21 pages; 15 visualizations on scoring, toss/chasing, teams, batting, bowling, venues, and wicket phases. Includes preprocessing choices and limitations. |
| A1 plan and prompt | `../Assignment1/new_data/IPL_Tableau_Data_Story_Plan.pdf`, `../Assignment1/new_data/DAS732_T1-26-27_A1.pdf` | A1 data story plan and official A1 requirements. |
| Existing notebook | `../Assignment1/data.ipynb` | KaggleHub acquisition/inspection notes; `assign1.ipynb` is empty. |

**A1 problem statement:** How has T20 cricket evolved in the IPL, and what batting, bowling, strategic, and venue factors help explain match outcomes? Its existing visualizations are described in the report; the report claims 15 views and supplies league, team, player, and venue inferences. A3 will reuse the IPL source and valid data definitions, while adding a new six-over chase-state question, analysis, clustering, and supervised prediction. Existing A1 numeric claims will be recomputed before any use.

## Assignment 2: gridMET and Infovis

`../Assignment2` contains the official A2 prompt, a team report, preparation scripts, figure outputs, raw and processed gridMET NetCDF files for January–March 2020, and an `Member1` IPL-derived set of match/player/team tables. A2 itself combines meteorological SciVis and multiple Infovis tasks. The climate slice is spatial-temporal and has no material link to IPL chase outcomes, so it is not selected as supplemental data. The A2 IPL-derived tables are secondary processed copies and are unnecessary when A1 raw event tables are available.

## Dataset and analysis feasibility

`../Assignment2/Member1/correct_data/` matches the selected A1 `new_data` snapshot in the five table shapes and is not a separate source. A2 also contains an IPL-derived node-link network with preprocessing and layout scripts; that network task does not add match-state variables needed for this chase question. The A1 and A2 notebooks/scripts/reports and visible figure outputs were inventoried; no A2 notebook provides additional source data for this analysis.

The three A2 AI-disclosure forms name K V Shashank Pai (BT2024250), Adithya Kommuri (BT2024246), and Nishanth Karamsetty (BT2024094). These are provisionally listed in the A3 report as the prior-course group; verify that A3 membership is unchanged before submission.

- The A1 match and delivery tables have complete match-ID coverage in both directions.
- After filtering to regular second-innings data, resolved normal matches without D/L adjustment, a standard match of at least seven overs, and at least 36 legal balls in overs 0–5, an initial feasibility check produced 1,194 match-level six-over states (649 chases won, 545 lost). The pipeline will recompute and validate these values.
- Preliminary pressure quartiles show substantially different chase-success proportions (approximately 86.8% at the lowest required-rate quartile and 16.1% at the highest). This supports a testable target-pressure transformation; it is a scoping result, not a final pipeline result.
- Missingness appears in optional match and delivery-event fields. The delivery table has exact repeated rows and repeated apparent natural keys; these require contextual review and will not be blindly dropped.

## Reusable work and limitations

- Reuse A1 team/date/innings definitions only after validating them against raw data.
- Do not treat A1's prior visualizations or report as new A3 contribution.
- A2 climate scripts, NetCDF processing, and unrelated plots are not reusable for this IPL question.
- A1 data is accessed by relative sibling path; the A3 folder will document this prerequisite rather than duplicate large raw files. The A1 report will be copied unchanged to the A3 appendix for submission completeness.
- No A3 implementation existed at inspection time. The initial A3 deliverable PDF is the only file originally in this project folder.
