"""Count-aware donor-level pseudobulk differential expression with PyDESeq2."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats
from scipy import sparse


def _to_dense(matrix: object) -> np.ndarray:
    if sparse.issparse(matrix):
        return np.asarray(matrix.toarray())
    return np.asarray(matrix)


def aggregate_pseudobulk_counts(
    counts: object,
    obs: pd.DataFrame,
    gene_names: Sequence[str],
    *,
    subtype_key: str,
    subtype: str,
    condition_key: str,
    donor_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Sum raw counts into donor × condition samples for one subtype.

    Returns the sample-by-gene count matrix, sample metadata, and a small table
    reporting how many cells contributed to each pseudobulk sample.
    """

    required = [subtype_key, condition_key, donor_key]
    missing = [column for column in required if column not in obs]
    if missing:
        raise ValueError(f"Missing pseudobulk metadata columns: {', '.join(missing)}")
    mask = obs[subtype_key].astype(str).eq(str(subtype)).to_numpy()
    if not mask.any():
        raise ValueError(f"No cells were annotated as subtype {subtype!r}")
    selected_obs = obs.loc[mask, required].copy()
    selected_counts = _to_dense(counts[mask])
    if selected_counts.ndim != 2 or selected_counts.shape[1] != len(gene_names):
        raise ValueError("Count matrix shape does not match gene_names")

    group_frame = selected_obs[[donor_key, condition_key]].astype(str)
    group_ids = group_frame[donor_key] + "__" + group_frame[condition_key]
    categories, inverse = np.unique(group_ids.to_numpy(), return_inverse=True)
    aggregated = np.zeros((len(categories), selected_counts.shape[1]), dtype=np.int64)
    np.add.at(aggregated, inverse, selected_counts.astype(np.int64, copy=False))

    sample_rows: list[dict[str, object]] = []
    for index, sample_id in enumerate(categories):
        first = int(np.flatnonzero(inverse == index)[0])
        sample_rows.append(
            {
                "sample_id": sample_id,
                donor_key: str(group_frame.iloc[first][donor_key]),
                condition_key: str(group_frame.iloc[first][condition_key]),
                "n_cells": int((inverse == index).sum()),
            }
        )
    sample_info = pd.DataFrame(sample_rows).set_index("sample_id")
    counts_df = pd.DataFrame(aggregated, index=sample_info.index, columns=list(gene_names))
    metadata = sample_info[[donor_key, condition_key]].copy()
    return counts_df, metadata, sample_info.reset_index()


def pydeseq2_de(
    counts: object,
    obs: pd.DataFrame,
    gene_names: Sequence[str],
    *,
    subtype_key: str,
    subtype: str,
    condition_key: str,
    condition_a: str,
    condition_b: str,
    donor_key: str,
    min_donors_per_condition: int = 4,
    min_total_count: int = 10,
    n_cpus: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run a DESeq2-style count model on donor-level pseudobulk samples.

    A paired/repeated-donor design uses ``~donor + condition``.  If donors are
    nested in condition, the valid design is ``~condition``.  Genes below
    ``min_total_count`` are returned as not testable rather than silently lost.
    """

    counts_df, metadata, sample_info = aggregate_pseudobulk_counts(
        counts,
        obs,
        gene_names,
        subtype_key=subtype_key,
        subtype=subtype,
        condition_key=condition_key,
        donor_key=donor_key,
    )
    metadata[condition_key] = metadata[condition_key].astype(str)
    observed_conditions = set(metadata[condition_key])
    missing_conditions = {str(condition_a), str(condition_b)} - observed_conditions
    if missing_conditions:
        raise ValueError(f"Missing condition(s) after pseudobulk aggregation: {missing_conditions}")
    donor_counts = metadata.groupby(condition_key, observed=True)[donor_key].nunique()
    for condition in (str(condition_a), str(condition_b)):
        available = int(donor_counts.get(condition, 0))
        if available < min_donors_per_condition:
            raise ValueError(
                f"Condition {condition!r} has {available} donors for {subtype}; "
                f"need at least {min_donors_per_condition}"
            )

    testable = (counts_df.sum(axis=0) >= min_total_count) & (counts_df.gt(0).sum(axis=0) >= 2)
    if int(testable.sum()) < 2:
        raise ValueError("Fewer than two genes pass pseudobulk count filters")
    filtered = counts_df.loc[:, testable].astype(int)

    conditions_per_donor = metadata.groupby(donor_key, observed=True)[condition_key].nunique()
    paired = bool((conditions_per_donor >= 2).any())
    design = f"~{donor_key} + {condition_key}" if paired else f"~{condition_key}"
    dds = DeseqDataSet(
        counts=filtered,
        metadata=metadata,
        design=design,
        fit_type="mean",
        size_factors_fit_type="poscounts",
        refit_cooks=False,
        min_replicates=min_donors_per_condition,
        n_cpus=n_cpus,
        quiet=True,
        low_memory=True,
    )
    dds.deseq2()
    stats = DeseqStats(
        dds,
        contrast=[condition_key, str(condition_b), str(condition_a)],
        alpha=0.05,
        cooks_filter=False,
        independent_filter=True,
        n_cpus=n_cpus,
        quiet=True,
    )
    stats.summary()
    raw_result = stats.results_df.copy()
    raw_result.index.name = "gene"
    result = raw_result.reset_index().rename(
        columns={
            "baseMean": "base_mean",
            "log2FoldChange": "log2_fold_change",
            "lfcSE": "lfc_se",
            "pvalue": "p_value",
            "padj": "p_adj",
        }
    )
    result["testable"] = True
    result["method"] = "PyDESeq2 donor-level pseudobulk"
    result["subtype"] = str(subtype)
    result["contrast"] = f"{condition_b} vs {condition_a}"
    result["design"] = design

    untested_genes = counts_df.columns[~testable]
    if len(untested_genes):
        untested = pd.DataFrame(
            {
                "gene": untested_genes,
                "base_mean": np.nan,
                "log2_fold_change": np.nan,
                "lfc_se": np.nan,
                "stat": np.nan,
                "p_value": np.nan,
                "p_adj": np.nan,
                "testable": False,
                "method": "PyDESeq2 donor-level pseudobulk",
                "subtype": str(subtype),
                "contrast": f"{condition_b} vs {condition_a}",
                "design": design,
            }
        )
        result = pd.concat([result, untested], ignore_index=True)
    result["significant_fdr_0_05"] = result["p_adj"].lt(0.05).fillna(False)
    result = result.sort_values(["p_adj", "p_value"], na_position="last").reset_index(drop=True)
    return result, sample_info
