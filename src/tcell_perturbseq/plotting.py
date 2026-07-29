"""Four compact figures for the official supplementary-table workflow."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tcell_perturbseq.analysis import AnalysisResults
from tcell_perturbseq.config import AnalysisConfig

plt.switch_backend("Agg")

CONDITION_COLORS = {
    "Rest": "#2563EB",
    "Stim8hr": "#D97706",
    "Stim48hr": "#7C3AED",
}


def _finish(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _empty_figure(path: Path, *, title: str, message: str) -> Path:
    fig, axis = plt.subplots(figsize=(8, 3.5))
    axis.axis("off")
    axis.set_title(title, fontweight="bold")
    axis.text(0.5, 0.5, message, ha="center", va="center", transform=axis.transAxes)
    return _finish(fig, path)


def plot_filter_funnel(funnel: pd.DataFrame, path: Path) -> Path:
    """Show how many perturbation-condition rows survive each sequential gate."""

    fig, axis = plt.subplots(figsize=(11, 5.2))
    for condition_index, (condition, group) in enumerate(
        funnel.groupby("culture_condition", sort=False)
    ):
        ordered = group.sort_values("stage_order")
        axis.plot(
            ordered["stage_order"],
            ordered["n_rows"],
            marker="o",
            linewidth=2,
            label=condition,
            color=CONDITION_COLORS.get(str(condition), "#4B5563"),
        )
        final = ordered.iloc[-1]
        axis.annotate(
            f"{int(final['n_rows']):,}",
            (final["stage_order"], final["n_rows"]),
            xytext=(8, 5 + condition_index * 9),
            textcoords="offset points",
            ha="left",
            fontsize=8,
            color=CONDITION_COLORS.get(str(condition), "#4B5563"),
            fontweight="bold",
        )
    stage_labels = (
        funnel.sort_values("stage_order")
        .drop_duplicates("stage_order")
        .set_index("stage_order")["stage"]
    )
    axis.set_xticks(stage_labels.index, stage_labels.str.replace("_", " "), rotation=24, ha="right")
    axis.set_yscale("log")
    axis.set_ylabel("Perturbation-condition rows (log scale)")
    axis.set_title("Official screen: transparent source-QC filter funnel", fontweight="bold")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(title="Condition", frameon=False)
    fig.tight_layout()
    return _finish(fig, path)


def plot_top_candidates(
    top_candidates: pd.DataFrame,
    path: Path,
    *,
    conditions: tuple[str, ...],
    display_n: int = 10,
) -> Path:
    """Plot the highest within-condition geometric-mean priority scores."""

    if top_candidates.empty:
        return _empty_figure(
            path,
            title="Top source-QC candidates",
            message="No perturbations passed all hard gates.",
        )
    fig, axes = plt.subplots(1, len(conditions), figsize=(15, 5.5), sharex=True)
    axes_array = np.atleast_1d(axes)
    for axis, condition in zip(axes_array, conditions, strict=True):
        subset = (
            top_candidates.loc[top_candidates["culture_condition"].eq(condition)]
            .nsmallest(display_n, "rank_within_condition")
            .sort_values("priority_score")
        )
        axis.barh(
            subset["gene"],
            subset["priority_score"],
            color=CONDITION_COLORS.get(condition, "#4B5563"),
            alpha=0.88,
        )
        axis.set_title(condition)
        axis.set_xlim(0, 1.03)
        axis.grid(axis="x", alpha=0.2)
        axis.set_xlabel("Priority score")
    fig.suptitle(
        "Top source-QC candidates by condition\n"
        "geometric mean of three within-condition percentile ranks",
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()
    return _finish(fig, path)


def plot_cross_condition_scores(
    cross_condition: pd.DataFrame,
    path: Path,
    *,
    conditions: tuple[str, ...],
    display_n: int = 25,
) -> Path:
    """Heatmap condition scores for genes with source-QC passes in all three conditions."""

    if cross_condition.empty:
        return _empty_figure(
            path,
            title="Cross-condition candidate scores",
            message="No gene passed source QC in all three conditions.",
        )
    subset = cross_condition.nsmallest(display_n, "cross_condition_rank").copy()
    columns = [f"{condition}_priority_score" for condition in conditions]
    matrix = subset[columns].to_numpy(dtype=float)
    fig_height = max(5.0, 0.32 * len(subset) + 1.8)
    fig, axis = plt.subplots(figsize=(7.5, fig_height))
    image = axis.imshow(matrix, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    axis.set_xticks(range(len(conditions)), conditions)
    axis.set_yticks(range(len(subset)), subset["gene"])
    axis.set_xlabel("Culture condition")
    axis.set_ylabel("Gene")
    axis.set_title(
        "Reproducible candidates across all conditions\n"
        "ordered by the minimum condition-specific priority score",
        fontweight="bold",
    )
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            text_color = "white" if value < 0.55 else "black"
            axis.text(column, row, f"{value:.2f}", ha="center", va="center", color=text_color)
    colorbar = fig.colorbar(image, ax=axis, pad=0.03)
    colorbar.set_label("Within-condition priority score")
    fig.tight_layout()
    return _finish(fig, path)


def plot_validation_deltas(deltas: pd.DataFrame, path: Path) -> Path:
    """Show donor-matched IL10 and IL21 changes relative to each donor's mean NTC."""

    if deltas.empty:
        return _empty_figure(
            path,
            title="Arrayed follow-up",
            message="No non-control arrayed measurements were available.",
        )
    perturbations = sorted(deltas["perturbation"].astype(str).unique())
    donors = sorted(deltas["donor"].astype(str).unique())
    donor_index = {donor: index for index, donor in enumerate(donors)}
    color_map = plt.get_cmap("tab10")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharex=True)
    metrics = (
        ("IL10_delta_vs_donor_NTC", "IL10+ cells: percentage-point delta"),
        ("IL21_delta_vs_donor_NTC", "IL21+ cells: percentage-point delta"),
    )
    x_lookup = {name: index for index, name in enumerate(perturbations)}
    for axis, (metric, ylabel) in zip(axes, metrics, strict=True):
        for donor in donors:
            subset = deltas[deltas["donor"].astype(str).eq(donor)]
            offset = (donor_index[donor] - (len(donors) - 1) / 2) * 0.055
            x_values = [x_lookup[str(name)] + offset for name in subset["perturbation"]]
            axis.scatter(
                x_values,
                subset[metric],
                s=38,
                alpha=0.85,
                color=color_map(donor_index[donor] % 10),
                label=donor,
            )
        means = deltas.groupby("perturbation", observed=True)[metric].mean().reindex(perturbations)
        axis.scatter(
            range(len(perturbations)),
            means,
            marker="D",
            s=55,
            facecolor="white",
            edgecolor="#111827",
            linewidth=1.2,
            label="descriptive mean",
            zorder=5,
        )
        axis.axhline(0, color="#374151", linestyle="--", linewidth=1)
        axis.set_xticks(range(len(perturbations)), perturbations, rotation=45, ha="right")
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.2)
    handles, labels = axes[1].get_legend_handles_labels()
    axes[1].legend(handles, labels, title="Donor", frameon=False, bbox_to_anchor=(1.02, 1))
    fig.suptitle(
        "Arrayed IL10/IL21 follow-up: donor-matched descriptive deltas\n"
        "Each point subtracts that donor's mean NTC/NTC1/NTC2/NTC3 value; no p-values",
        fontweight="bold",
        y=1.03,
    )
    fig.tight_layout()
    return _finish(fig, path)


def write_figures(
    results: AnalysisResults,
    config: AnalysisConfig,
) -> list[Path]:
    """Write the four registered figures and return their paths."""

    root = config.output_dir / "figures"
    return [
        plot_filter_funnel(results.filter_funnel, root / "01_filter_funnel.png"),
        plot_top_candidates(
            results.top_candidates_by_condition,
            root / "02_top_candidates.png",
            conditions=config.conditions,
        ),
        plot_cross_condition_scores(
            results.cross_condition_candidates,
            root / "03_cross_condition_scores.png",
            conditions=config.conditions,
        ),
        plot_validation_deltas(
            results.validation_donor_deltas,
            root / "04_arrayed_validation_deltas.png",
        ),
    ]
