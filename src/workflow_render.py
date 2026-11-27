"""Render the conceptual and unrolled visual analytics workflow."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def render_workflow(output: Path) -> Path:
    """Draw the cyclic workflow and its project-specific unrolled execution."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 10), constrained_layout=True)
    ax.set_xlim(-0.8, 15.5)
    ax.set_ylim(-0.8, 10.8)
    ax.axis("off")

    colors = {"data": "#E8EEF3", "view": "#DCEFEB", "model": "#E6E3F3", "knowledge": "#FFF1D6"}

    def node(x: float, y: float, w: float, h: float, label: str, fill: str,
             *, fontsize: float = 9.2) -> tuple[float, float]:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.16",
                             facecolor=fill, edgecolor="#567184", linewidth=1.25, zorder=2)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                color="#17324D", fontsize=fontsize, zorder=3)
        return x + w / 2, y + h / 2

    def edge(a: tuple[float, float], b: tuple[float, float], *, rad: float = 0,
             color: str = "#567184", label: str | None = None,
             label_xy: tuple[float, float] | None = None, lw: float = 1.5) -> None:
        patch = FancyArrowPatch(a, b, arrowstyle="<|-|>", mutation_scale=12,
                                connectionstyle=f"arc3,rad={rad}", color=color,
                                linewidth=lw, shrinkA=26, shrinkB=26, zorder=1)
        ax.add_patch(patch)
        if label and label_xy:
            ax.text(*label_xy, label, ha="center", va="center", fontsize=8.3,
                    color=color, bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none"})

    def self_loop(center: tuple[float, float], *, color: str = "#567184") -> None:
        x, y = center
        ax.add_patch(FancyArrowPatch((x - .22, y + .34), (x + .22, y + .34),
                                     arrowstyle="<|-|>", mutation_scale=10,
                                     connectionstyle="arc3,rad=-1.5", color=color,
                                     linewidth=1.25, shrinkA=0, shrinkB=0, zorder=1))

    ax.text(0, 10.45, "DAS732 A3 | Visual analytics workflow", fontsize=17,
            color="#17324D", fontweight="bold", ha="left")
    ax.text(0, 10.12, "A general interactive cycle, followed by the project's concrete end-to-end path",
            fontsize=10, color="#536879", ha="left")

    # General workflow: two-way collaboration, with refinement possible inside every stage.
    ax.text(0, 9.55, "1  |  CYCLIC WORKFLOW", fontsize=11, color="#17324D", fontweight="bold")
    cyc = {
        "data": node(.6, 7.35, 2.35, .78, "Data", colors["data"], fontsize=11),
        "view": node(5.0, 8.1, 2.55, .78, "Visualization", colors["view"], fontsize=11),
        "knowledge": node(10.7, 7.35, 2.55, .78, "Knowledge\n(inferences)", colors["knowledge"], fontsize=10),
        "model": node(5.0, 6.25, 2.55, .78, "Model", colors["model"], fontsize=11),
    }
    edge(cyc["data"], cyc["view"], rad=-.08)
    edge(cyc["view"], cyc["knowledge"], rad=-.08)
    edge(cyc["knowledge"], cyc["model"], rad=-.08)
    edge(cyc["model"], cyc["data"], rad=-.08, color="#C45849", label="feedback to data", label_xy=(3.85, 6.9))
    edge(cyc["view"], cyc["model"], rad=.12)
    for c in cyc.values():
        self_loop(c)
    ax.text(14.0, 7.1, "Bidirectional flows\nconnect the stages.\nSelf loops represent\nrefinement within\na stage.",
            ha="left", va="center", fontsize=8.5, color="#536879", linespacing=1.35)

    # Unroll the actual feedback into successive, observable steps.
    ax.text(0, 5.55, "2  |  UNROLLED PROJECT WORKFLOW", fontsize=11,
            color="#17324D", fontweight="bold")
    w, h = 2.42, .88
    x_positions = [.1, 3.15, 6.2, 9.25, 12.3]
    row_y = [4.0, 2.25]
    top = [
        ("Data · iteration 1\nA1 match + delivery tables", colors["data"]),
        ("Visualization · initial\nSix-over runs and wickets", colors["view"]),
        ("Model + analysis\nRates, K-means, logistic", colors["model"]),
        ("Visualization · results\nOutcome patterns + comparison", colors["view"]),
        ("Knowledge · inference 1\nRaw state omits target context", colors["knowledge"]),
    ]
    bottom = [
        ("Data · iteration 2\nAdd target-relative features", colors["data"]),
        ("Visualization · revised\nRequired-rate outcome gradient", colors["view"]),
        ("Model · iteration 2\nPressure-aware clustering + logistic", colors["model"]),
        ("Visualization · evaluation\nProfiles + held-out comparison", colors["view"]),
        ("Knowledge · final inference\nInterpret findings and limits", colors["knowledge"]),
    ]
    rows: list[list[tuple[float, float]]] = []
    for y, items in zip(row_y, (top, bottom)):
        centers = []
        for x, (label, fill) in zip(x_positions, items):
            centers.append(node(x, y, w, h, label, fill, fontsize=8.25))
        rows.append(centers)
    for row in rows:
        for a, b in zip(row, row[1:]):
            edge(a, b, color="#567184", lw=1.35)
    # The inference is made explicit as a data change that launches the next pass.
    edge(rows[0][-1], rows[1][0], rad=-.06, color="#C45849",
         label="Feedback loop: inference changes dataset", label_xy=(7.3, 3.25), lw=2.0)
    ax.text(.1, 1.38,
            "Implementation: src/data_loading.py → src/preprocessing.py → src/visualization.py → src/modeling.py / src/analysis.py → "
            "src/transformation.py → src/visualization.py → run_all.py",
            ha="left", va="center", fontsize=8.2, color="#536879")
    ax.text(.1, .88,
            "The first inference motivates runs remaining and required run rate; the transformed rows retain the same matches and outcomes.",
            ha="left", va="center", fontsize=8.7, color="#536879")
    ax.text(.1, .35, "The project formalizes how evidence guides the next analysis step, from data preparation through a documented final interpretation.",
            ha="left", va="center", fontsize=8.7, color="#536879")

    fig.savefig(output, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output
