"""Scanpy preprocessing, CD8 gating, module scoring, and subtype annotation.

Raw integer counts remain untouched in ``adata.layers['counts']``.  ``adata.X``
is transformed only on a copied, gated object for visualization and scoring.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse


def _dense_column(matrix: object, index: int) -> np.ndarray:
    """Return one matrix column as a flat NumPy array."""

    column = matrix[:, index]
    if sparse.issparse(column):
        return np.asarray(column.toarray()).ravel()
    return np.asarray(column).ravel()


def _resolution_key(prefix: str, resolution: float) -> str:
    token = f"{resolution:g}".replace(".", "_")
    return f"{prefix}_{token}"


def calculate_qc_metrics(adata: ad.AnnData, counts_layer: str = "counts") -> pd.DataFrame:
    """Calculate transparent per-cell QC metrics directly from raw counts."""

    if counts_layer not in adata.layers:
        raise ValueError(f"Raw-count layer {counts_layer!r} was not found")
    counts = adata.layers[counts_layer]
    total = np.asarray(counts.sum(axis=1)).ravel()
    if sparse.issparse(counts):
        detected = np.asarray((counts > 0).sum(axis=1)).ravel()
    else:
        detected = np.count_nonzero(np.asarray(counts) > 0, axis=1)
    mt_mask = np.asarray(adata.var_names.str.upper().str.startswith("MT-"))
    mt_counts = np.asarray(counts[:, mt_mask].sum(axis=1)).ravel() if mt_mask.any() else 0.0
    pct_mito = np.divide(
        mt_counts,
        total,
        out=np.zeros_like(total, dtype=float),
        where=total > 0,
    ) * 100.0
    return pd.DataFrame(
        {
            "total_counts": total,
            "n_genes_by_counts": detected,
            "pct_counts_mito": pct_mito,
        },
        index=adata.obs_names.copy(),
    )


def qc_and_cd8_gate(
    adata: ad.AnnData,
    *,
    counts_layer: str = "counts",
    min_genes: int = 10,
    max_genes: int | None = None,
    max_pct_mito: float = 20.0,
    min_total_counts: int = 1,
) -> tuple[ad.AnnData, pd.DataFrame]:
    """Apply pre-registered QC and the ``CD8A/B+ and CD4-`` operational gate.

    The RNA gate is intentionally simple and auditable.  A zero count can also
    be caused by dropout, so real projects should inspect the returned gate
    summary and, when available, compare it with expert cell-type annotations.
    """

    qc = calculate_qc_metrics(adata, counts_layer)
    qc_pass = (
        (qc["n_genes_by_counts"] >= min_genes)
        & (qc["pct_counts_mito"] <= max_pct_mito)
        & (qc["total_counts"] >= min_total_counts)
    )
    if max_genes is not None:
        qc_pass &= qc["n_genes_by_counts"] <= max_genes

    required = ["CD8A", "CD8B", "CD4"]
    missing = [gene for gene in required if gene not in adata.var_names]
    if missing:
        raise ValueError(f"Cannot apply the CD8 gate; missing genes: {', '.join(missing)}")
    counts = adata.layers[counts_layer]
    gene_index = {gene: adata.var_names.get_loc(gene) for gene in required}
    cd8a = _dense_column(counts, gene_index["CD8A"])
    cd8b = _dense_column(counts, gene_index["CD8B"])
    cd4 = _dense_column(counts, gene_index["CD4"])
    cd8_gate = ((cd8a > 0) | (cd8b > 0)) & (cd4 == 0)

    decisions = qc.copy()
    decisions["qc_pass"] = qc_pass
    decisions["cd8_gate_pass"] = cd8_gate
    decisions["analysis_pass"] = qc_pass & cd8_gate
    gated = adata[decisions["analysis_pass"].to_numpy()].copy()
    gated.uns["gate_summary"] = {
        "input_cells": int(adata.n_obs),
        "qc_pass_cells": int(qc_pass.sum()),
        "cd8_gate_pass_cells": int(cd8_gate.sum()),
        "analysis_cells": int(gated.n_obs),
        "gate": "(CD8A > 0 OR CD8B > 0) AND CD4 == 0 on raw counts",
        "dropout_caveat": "A zero RNA count is an operational threshold, not proof of absence.",
    }
    if gated.n_obs < 20:
        raise ValueError(f"Only {gated.n_obs} cells survived QC and CD8 gating; need at least 20")
    return gated, decisions


def normalize_embed_and_cluster(
    adata: ad.AnnData,
    *,
    counts_layer: str = "counts",
    resolutions: Sequence[float] = (0.4, 0.6, 0.8, 1.0),
    seed: int = 17,
    n_neighbors: int = 15,
) -> ad.AnnData:
    """Normalize, compute PCA/neighbors/UMAP, and run the Leiden sweep."""

    result = adata.copy()
    result.X = result.layers[counts_layer].copy()
    sc.pp.normalize_total(result, target_sum=10_000)
    sc.pp.log1p(result)
    result.layers["lognorm"] = result.X.copy()

    n_top_genes = min(2_000, max(1, result.n_vars - 1))
    sc.pp.highly_variable_genes(result, n_top_genes=n_top_genes, flavor="seurat")
    n_hvg = int(result.var["highly_variable"].sum())
    if n_hvg < 3:
        result.var["highly_variable"] = True
        n_hvg = result.n_vars
    n_comps = max(2, min(30, result.n_obs - 1, n_hvg - 1))
    # Sparse, non-zero-centred PCA avoids densifying a real single-cell matrix.
    sc.tl.pca(
        result,
        n_comps=n_comps,
        zero_center=False,
        svd_solver="randomized",
        mask_var="highly_variable",
        random_state=seed,
    )
    sc.pp.neighbors(
        result,
        n_neighbors=max(2, min(n_neighbors, result.n_obs - 1)),
        n_pcs=n_comps,
        random_state=seed,
    )
    sc.tl.umap(result, random_state=seed)
    for resolution in resolutions:
        sc.tl.leiden(
            result,
            resolution=float(resolution),
            key_added=_resolution_key("leiden", float(resolution)),
            random_state=seed,
            flavor="igraph",
            n_iterations=2,
        )
    result.uns["preprocessing"] = {
        "normalization": "library-size normalize to 10,000 counts then log1p",
        "pca_components": n_comps,
        "neighbors": max(2, min(n_neighbors, result.n_obs - 1)),
        "resolutions": [float(value) for value in resolutions],
        "seed": int(seed),
    }
    return result


def _score_genes(
    adata: ad.AnnData,
    genes: Sequence[str],
    score_name: str,
    *,
    seed: int,
) -> list[str]:
    present = [gene for gene in genes if gene in adata.var_names]
    if not present:
        raise ValueError(f"None of the genes for {score_name!r} are present")
    gene_pool = [gene for gene in adata.var_names if gene not in present]
    if len(gene_pool) < 2:
        raise ValueError("At least two non-panel genes are required for control-gene scoring")
    ctrl_size = max(1, min(25, len(gene_pool)))
    sc.tl.score_genes(
        adata,
        gene_list=present,
        gene_pool=list(adata.var_names),
        ctrl_size=ctrl_size,
        n_bins=max(2, min(10, len(gene_pool) // 5)),
        score_name=score_name,
        random_state=seed,
        ctrl_as_ref=False,
        use_raw=False,
    )
    return present


def score_and_annotate_subtypes(
    adata: ad.AnnData,
    *,
    marker_panels: Mapping[str, Sequence[str]],
    negative_marker_rules: Mapping[str, Sequence[str]] | None = None,
    min_positive_markers: Mapping[str, int] | None = None,
    exhaustion_genes: Sequence[str],
    resolutions: Sequence[float],
    primary_resolution: float,
    seed: int = 17,
    min_marker_margin: float = 0.0,
) -> tuple[ad.AnnData, pd.DataFrame]:
    """Score marker panels and assign each Leiden cluster deterministically.

    Each cluster receives the subtype with the highest mean marker score.  If
    the leading score does not beat the runner-up by ``min_marker_margin``, the
    label is ``ambiguous`` rather than a forced biological assertion.
    """

    result = adata.copy()
    if "lognorm" not in result.layers:
        raise ValueError("Expected a normalized 'lognorm' layer")
    scaled = result.X
    result.X = result.layers["lognorm"].copy()
    score_columns: dict[str, str] = {}
    negative_score_columns: dict[str, str] = {}
    panel_presence: dict[str, list[str]] = {}
    for subtype, genes in marker_panels.items():
        column = f"marker_score__{subtype}"
        panel_presence[subtype] = _score_genes(result, genes, column, seed=seed)
        score_columns[subtype] = column
    for subtype, genes in (negative_marker_rules or {}).items():
        column = f"negative_marker_score__{subtype}"
        _score_genes(result, genes, column, seed=seed)
        negative_score_columns[subtype] = column
    exhaustion_present = _score_genes(
        result,
        exhaustion_genes,
        "exhaustion_score",
        seed=seed,
    )
    result.X = scaled

    annotation_rows: list[dict[str, object]] = []
    for resolution in resolutions:
        cluster_key = _resolution_key("leiden", float(resolution))
        subtype_key = _resolution_key("subtype", float(resolution))
        if cluster_key not in result.obs:
            raise ValueError(f"Missing Leiden result {cluster_key!r}")
        cluster_scores = result.obs.groupby(cluster_key, observed=True)[
            [*score_columns.values(), *negative_score_columns.values()]
        ].mean()
        labels: dict[str, str] = {}
        for cluster, scores in cluster_scores.iterrows():
            cluster_mask = result.obs[cluster_key].astype(str).eq(str(cluster)).to_numpy()
            effective_scores: dict[str, float] = {}
            positive_counts: dict[str, int] = {}
            for candidate, column in score_columns.items():
                effective = float(scores[column])
                negative_column = negative_score_columns.get(candidate)
                if negative_column is not None:
                    effective -= max(0.0, float(scores[negative_column]))
                present_genes = panel_presence[candidate]
                positions = [result.var_names.get_loc(gene) for gene in present_genes]
                panel_matrix = result.layers["lognorm"][:, positions]
                global_means = np.asarray(panel_matrix.mean(axis=0)).ravel()
                cluster_means = np.asarray(panel_matrix[cluster_mask].mean(axis=0)).ravel()
                positive_count = int((cluster_means > global_means).sum())
                positive_counts[candidate] = positive_count
                required_count = (min_positive_markers or {}).get(candidate, 0)
                if positive_count < required_count:
                    effective = -np.inf
                effective_scores[candidate] = effective

            ranked = pd.Series(effective_scores).sort_values(ascending=False)
            subtype = str(ranked.index[0])
            margin = float(ranked.iloc[0] - ranked.iloc[1]) if len(ranked) > 1 else np.inf
            if margin < min_marker_margin:
                subtype = "ambiguous"
            labels[str(cluster)] = subtype
            row: dict[str, object] = {
                "resolution": float(resolution),
                "cluster": str(cluster),
                "subtype": subtype,
                "marker_margin": margin,
                "n_cells": int(cluster_mask.sum()),
            }
            row.update({name: float(scores[column]) for name, column in score_columns.items()})
            row.update(
                {f"effective_score__{name}": value for name, value in effective_scores.items()}
            )
            row.update(
                {
                    f"positive_markers_above_global__{name}": value
                    for name, value in positive_counts.items()
                }
            )
            row.update(
                {
                    f"negative_score__{name}": float(scores[column])
                    for name, column in negative_score_columns.items()
                }
            )
            annotation_rows.append(row)
        result.obs[subtype_key] = pd.Categorical(
            result.obs[cluster_key].astype(str).map(labels),
            categories=[*marker_panels.keys(), "ambiguous"],
        )

    primary_key = _resolution_key("subtype", float(primary_resolution))
    if primary_key not in result.obs:
        raise ValueError(f"Primary resolution {primary_resolution} is not in the sweep")
    result.obs["subtype"] = result.obs[primary_key].copy()
    result.uns["gene_panels"] = {
        "marker_panels_present": panel_presence,
        "exhaustion_genes_present": exhaustion_present,
        "annotation_rule": "highest cluster-mean marker score; ambiguous below margin",
        "min_marker_margin": float(min_marker_margin),
    }
    return result, pd.DataFrame(annotation_rows)


def subtype_key_for_resolution(resolution: float) -> str:
    """Public helper for resolution-specific subtype columns."""

    return _resolution_key("subtype", resolution)
