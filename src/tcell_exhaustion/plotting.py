"""Publication-style but learner-friendly figures for the triage workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PALETTE = {
    "memory_stem_like": "#3B82F6",
    "effector_memory": "#14B8A6",
    "effector_cytotoxic": "#F59E0B",
    "terminally_exhausted": "#DC2626",
    "ambiguous": "#9CA3AF",
}


def _finish(fig: plt.Figure, path: Path, *, simulated: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if simulated:
        fig.text(
            0.995,
            0.005,
            "SIMULATED DEMO — NOT BIOLOGICAL EVIDENCE",
            ha="right",
            va="bottom",
            fontsize=8,
            color="#991B1B",
            alpha=0.8,
        )
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_qc(qc: pd.DataFrame, path: Path, *, simulated: bool = False) -> Path:
    """Plot core QC distributions and the transparent pass/fail counts."""

    sns.set_theme(style="whitegrid", context="notebook")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.7))
    sns.histplot(qc["total_counts"], bins=35, ax=axes[0], color="#2563EB")
    axes[0].set_title("Library size")
    axes[0].set_xlabel("Raw counts per cell")
    sns.histplot(qc["n_genes_by_counts"], bins=30, ax=axes[1], color="#0F766E")
    axes[1].set_title("Genes detected")
    axes[1].set_xlabel("Genes with count > 0")
    sns.histplot(qc["pct_counts_mito"], bins=30, ax=axes[2], color="#B45309")
    axes[2].set_title("Mitochondrial fraction")
    axes[2].set_xlabel("Mitochondrial reads (%)")
    fig.suptitle("Cell quality control before CD8 gating", fontweight="bold", y=1.04)
    fig.tight_layout()
    return _finish(fig, path, simulated=simulated)


def plot_annotated_umap(
    adata: ad.AnnData,
    path: Path,
    *,
    subtype_key: str = "subtype",
    condition_key: str = "condition",
    simulated: bool = False,
) -> Path:
    """Create the required annotated CD8 UMAP and a condition companion panel."""

    if "X_umap" not in adata.obsm:
        raise ValueError("UMAP coordinates are missing")
    coords = np.asarray(adata.obsm["X_umap"])
    frame = pd.DataFrame(
        {
            "UMAP1": coords[:, 0],
            "UMAP2": coords[:, 1],
            "subtype": adata.obs[subtype_key].astype(str).to_numpy(),
            "condition": adata.obs[condition_key].astype(str).to_numpy(),
        }
    )
    sns.set_theme(style="white", context="notebook")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.scatterplot(
        data=frame,
        x="UMAP1",
        y="UMAP2",
        hue="subtype",
        palette=PALETTE,
        s=14,
        linewidth=0,
        alpha=0.8,
        ax=axes[0],
    )
    axes[0].set_title("Marker-defined CD8+ subtypes")
    sns.scatterplot(
        data=frame,
        x="UMAP1",
        y="UMAP2",
        hue="condition",
        palette="Set2",
        s=14,
        linewidth=0,
        alpha=0.8,
        ax=axes[1],
    )
    axes[1].set_title("The same cells, colored by condition")
    for axis in axes:
        axis.set_xticks([])
        axis.set_yticks([])
        axis.legend(frameon=False, fontsize=8, markerscale=1.4)
    fig.suptitle("Deliverable 1 — annotated CD8+ T-cell UMAP", fontweight="bold", y=1.02)
    fig.tight_layout()
    return _finish(fig, path, simulated=simulated)


def plot_exhaustion_violin(
    obs: pd.DataFrame,
    donor_stats: pd.DataFrame,
    path: Path,
    *,
    subtype_key: str,
    condition_key: str,
    donor_key: str | None,
    score_key: str = "exhaustion_score",
    simulated: bool = False,
) -> Path:
    """Plot cell distributions with donor means overlaid as the true replicates."""

    frame = obs.copy()
    frame[subtype_key] = frame[subtype_key].astype(str)
    frame[condition_key] = frame[condition_key].astype(str)
    order = [name for name in PALETTE if name in set(frame[subtype_key])]
    if not order:
        order = sorted(frame[subtype_key].unique())
    sns.set_theme(style="whitegrid", context="notebook")
    fig, ax = plt.subplots(figsize=(12, 5.5))
    sns.violinplot(
        data=frame,
        x=subtype_key,
        y=score_key,
        hue=condition_key,
        order=order,
        inner=None,
        cut=0,
        density_norm="width",
        palette="Set2",
        linewidth=0.7,
        alpha=0.45,
        ax=ax,
    )
    if donor_key and donor_key in frame:
        donor_means = (
            frame.groupby([donor_key, condition_key, subtype_key], observed=True)[score_key]
            .mean()
            .reset_index()
        )
        sns.stripplot(
            data=donor_means,
            x=subtype_key,
            y=score_key,
            hue=condition_key,
            order=order,
            dodge=True,
            palette="Set2",
            marker="o",
            size=5,
            edgecolor="black",
            linewidth=0.5,
            ax=ax,
        )
    handles, labels = ax.get_legend_handles_labels()
    unique: dict[str, Any] = {}
    for handle, label in zip(handles, labels, strict=False):
        unique.setdefault(label, handle)
    ax.legend(unique.values(), unique.keys(), title="Condition", frameon=False, loc="best")
    annotations = []
    for row in donor_stats.itertuples(index=False):
        subtype = getattr(row, "subtype", None)
        if subtype in order:
            q_value = getattr(row, "p_adj", np.nan)
            annotations.append(f"{subtype}: Δ={getattr(row, 'delta', np.nan):.2f}, q={q_value:.3g}")
    if annotations:
        ax.text(
            1.01,
            0.02,
            "Donor-aware tests\n" + "\n".join(annotations),
            transform=ax.transAxes,
            va="bottom",
            fontsize=8,
        )
    ax.set_title("Deliverable 2 — exhaustion score by subtype and condition", fontweight="bold")
    ax.set_xlabel("CD8+ subtype")
    ax.set_ylabel("Relative exhaustion module score")
    ax.tick_params(axis="x", rotation=18)
    fig.tight_layout()
    return _finish(fig, path, simulated=simulated)


def plot_volcano(
    de: pd.DataFrame,
    path: Path,
    *,
    exhaustion_genes: list[str] | tuple[str, ...],
    headline_subtype: str,
    simulated: bool = False,
) -> Path:
    """Plot all tested genes and highlight the pre-registered exhaustion panel."""

    frame = de.copy()
    frame["minus_log10_fdr"] = -np.log10(frame["p_adj"].clip(lower=np.finfo(float).tiny))
    frame["significant"] = frame["p_adj"] < 0.05
    frame["panel_gene"] = frame["gene"].isin(exhaustion_genes)
    sns.set_theme(style="whitegrid", context="notebook")
    fig, ax = plt.subplots(figsize=(8.5, 6))
    sns.scatterplot(
        data=frame,
        x="log2_fold_change",
        y="minus_log10_fdr",
        hue="significant",
        palette={False: "#9CA3AF", True: "#7C3AED"},
        s=25,
        alpha=0.75,
        linewidth=0,
        legend=False,
        ax=ax,
    )
    panel = frame[frame["panel_gene"]]
    ax.scatter(
        panel["log2_fold_change"],
        panel["minus_log10_fdr"],
        s=65,
        facecolors="#DC2626",
        edgecolors="white",
        linewidth=0.8,
        label="Exhaustion panel",
        zorder=4,
    )
    label_rows = pd.concat(
        [panel, frame.nsmallest(min(5, len(frame)), "p_adj")], ignore_index=True
    ).drop_duplicates("gene")
    for row in label_rows.itertuples(index=False):
        ax.annotate(
            row.gene,
            (row.log2_fold_change, row.minus_log10_fdr),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
        )
    ax.axhline(-np.log10(0.05), linestyle="--", color="#374151", linewidth=1)
    ax.axvline(0, color="#374151", linewidth=0.8)
    ax.set_xlabel("Pseudobulk log2 fold-change (B − A)")
    ax.set_ylabel("−log10(FDR)")
    ax.set_title(
        f"Deliverable 3 — donor-level pseudobulk DE\n{headline_subtype}",
        fontweight="bold",
    )
    ax.legend(frameon=False)
    fig.tight_layout()
    return _finish(fig, path, simulated=simulated)


def plot_robustness_table(
    robustness: pd.DataFrame,
    path: Path,
    *,
    simulated: bool = False,
) -> Path:
    """Render the four-row robustness table as a presentation-ready figure."""

    columns = [
        "resolution",
        "headline_subtype",
        "delta",
        "p_adj",
        "matching_direction",
        "passes_fdr",
        "robust",
    ]
    display = robustness[[column for column in columns if column in robustness]].copy()
    for column in ("delta", "p_adj"):
        if column in display:
            display[column] = display[column].map(
                lambda value: f"{value:.3g}" if pd.notna(value) else "NA"
            )
    display.columns = [column.replace("_", " ").title() for column in display.columns]
    fig_height = 1.8 + 0.45 * max(1, len(display))
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for (row, _column), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1F2937")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#F3F4F6")
    ax.set_title(
        "Deliverable 4 — resolution robustness of the headline claim",
        fontweight="bold",
        pad=16,
    )
    fig.tight_layout()
    return _finish(fig, path, simulated=simulated)
