"""Statistical primitives for the T-cell exhaustion verification workflow.

The functions in this module deliberately separate two levels of evidence:

* :func:`per_cell_de` is a fast, exploratory screen.  Cells from the same
  donor are not independent biological replicates, so its p-values must not
  be used for the final claim.
* :func:`pseudobulk_de` aggregates raw counts to donor-level samples before
  testing.  This is the stricter recomputation used by the reviewer table.

The implementation is intentionally small and transparent.  It is not a
replacement for a count-model package such as edgeR or DESeq2, but it gives a
defensible Welch-test baseline that is easy to audit and teach.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse, stats

_FDR_THRESHOLD = 0.05


def benjamini_hochberg(pvalues: Sequence[float] | np.ndarray | pd.Series) -> np.ndarray:
    """Adjust p-values with the Benjamini-Hochberg false-discovery procedure.

    Parameters
    ----------
    pvalues:
        Array-like p-values.  Any shape is accepted and preserved.  ``NaN``
        values represent tests that could not be performed; they remain
        ``NaN`` and are not counted in the number of hypotheses.

    Returns
    -------
    numpy.ndarray
        FDR-adjusted p-values in the original shape and order.

    Raises
    ------
    ValueError
        If a non-missing p-value is infinite or outside ``[0, 1]``.

    Notes
    -----
    The reverse cumulative minimum is what makes adjusted p-values monotone
    after values are put back into ranked order.
    """

    try:
        values = np.asarray(pvalues, dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError("pvalues must be numeric or NaN") from exc

    original_shape = values.shape
    flat = values.ravel()
    missing = np.isnan(flat)
    non_missing = flat[~missing]

    if np.any(~np.isfinite(non_missing)):
        raise ValueError("pvalues must be finite or NaN")
    if np.any((non_missing < 0.0) | (non_missing > 1.0)):
        raise ValueError("pvalues must lie in the closed interval [0, 1]")

    adjusted = np.full(flat.shape, np.nan, dtype=float)
    number_tested = non_missing.size
    if number_tested == 0:
        return adjusted.reshape(original_shape)

    valid_positions = np.flatnonzero(~missing)
    order = np.argsort(non_missing, kind="mergesort")
    ranked = non_missing[order]
    ranks = np.arange(1, number_tested + 1, dtype=float)
    ranked_adjusted = ranked * number_tested / ranks
    ranked_adjusted = np.minimum.accumulate(ranked_adjusted[::-1])[::-1]
    ranked_adjusted = np.clip(ranked_adjusted, 0.0, 1.0)

    adjusted_positions = valid_positions[order]
    adjusted[adjusted_positions] = ranked_adjusted
    return adjusted.reshape(original_shape)


def donor_module_statistics(
    obs: pd.DataFrame,
    subtype_key: str,
    condition_key: str,
    condition_a: Any,
    condition_b: Any,
    donor_key: str | None = None,
    score_key: str = "exhaustion_score",
) -> pd.DataFrame:
    """Compare an exhaustion score between conditions within every subtype.

    When ``donor_key`` is supplied, cell scores are first averaged for each
    donor-by-subtype-by-condition combination.  A two-sided Welch test then
    compares those donor means, with the effect and test statistic oriented as
    ``condition_b - condition_a``.  This prevents donors with more captured
    cells from receiving more statistical weight.

    If ``donor_key`` is ``None``, each cell is used as a unit and the result is
    explicitly labelled exploratory (``donor_aware == False``).  This fallback
    is useful for datasets without donor metadata but must not be presented as
    donor-verified evidence.

    At least two independent units are required in each condition.  P-values
    are adjusted together across all returned subtypes.

    Returns
    -------
    pandas.DataFrame
        One row per observed subtype.  ``delta`` and ``t_statistic`` are
        positive when condition B is higher.  ``test_status`` is one of
        ``SIGNIFICANT``, ``NOT_SIGNIFICANT``, or ``NOT_TESTABLE``.
    """

    frame = _validate_obs(
        obs,
        required=[subtype_key, condition_key, score_key]
        + ([] if donor_key is None else [donor_key]),
        condition_a=condition_a,
        condition_b=condition_b,
    )

    working = frame.loc[
        frame[subtype_key].notna()
        & frame[condition_key].isin([condition_a, condition_b])
        & frame[score_key].notna()
    ].copy()
    working[score_key] = pd.to_numeric(working[score_key], errors="coerce")
    working = working.loc[np.isfinite(working[score_key].to_numpy(dtype=float))].copy()

    if donor_key is None:
        working["__analysis_unit"] = np.arange(len(working), dtype=np.int64)
        unit_key = "__analysis_unit"
        donor_aware = False
        analysis_unit = "cell (exploratory; donor_key not supplied)"
    else:
        working = working.loc[working[donor_key].notna()].copy()
        unit_key = donor_key
        donor_aware = True
        analysis_unit = "donor mean"

    subtypes = list(pd.unique(working[subtype_key]))
    if not subtypes:
        return _empty_module_result()

    unit_means = (
        working.groupby(
            [subtype_key, condition_key, unit_key], observed=True, sort=False, dropna=False
        )[score_key]
        .mean()
        .rename("unit_mean")
        .reset_index()
    )

    rows: list[dict[str, Any]] = []
    for subtype in subtypes:
        subtype_means = unit_means.loc[unit_means[subtype_key] == subtype]
        values_a = subtype_means.loc[
            subtype_means[condition_key] == condition_a, "unit_mean"
        ].to_numpy(dtype=float)
        values_b = subtype_means.loc[
            subtype_means[condition_key] == condition_b, "unit_mean"
        ].to_numpy(dtype=float)
        statistic, p_value = _welch_test(values_a, values_b)

        mean_a = _safe_mean(values_a)
        mean_b = _safe_mean(values_b)
        rows.append(
            {
                "subtype": subtype,
                "condition_a": condition_a,
                "condition_b": condition_b,
                "mean_a": mean_a,
                "mean_b": mean_b,
                "delta": mean_b - mean_a if np.isfinite(mean_a) and np.isfinite(mean_b) else np.nan,
                "n_units_a": int(values_a.size),
                "n_units_b": int(values_b.size),
                # Kept as explicit columns because these names are convenient
                # in figures.  In fallback mode they count cells, not donors;
                # ``donor_aware`` prevents that distinction being hidden.
                "n_donors_a": int(values_a.size),
                "n_donors_b": int(values_b.size),
                "t_statistic": statistic,
                "p_value": p_value,
                "donor_aware": donor_aware,
                "analysis_unit": analysis_unit,
            }
        )

    result = pd.DataFrame(rows)
    result["p_adj"] = benjamini_hochberg(result["p_value"].to_numpy(dtype=float))
    result["significant"] = result["p_adj"].lt(_FDR_THRESHOLD).fillna(False)
    result["test_status"] = _test_status(result["p_adj"])
    return result


def pseudobulk_de(
    counts: Any,
    obs: pd.DataFrame,
    gene_names: Sequence[Any],
    subtype_key: str,
    headline_subtype: Any,
    condition_key: str,
    condition_a: Any,
    condition_b: Any,
    donor_key: str,
) -> pd.DataFrame:
    """Run donor-level pseudobulk differential expression for one subtype.

    Raw counts are summed for every donor-by-condition sample within
    ``headline_subtype``.  Each aggregate is converted to ``log2(CPM + 1)``
    and a two-sided Welch test compares donor aggregates in condition B with
    those in condition A.  The reported ``log2fc`` is the difference between
    mean donor log2-CPM values (B minus A), matching the test orientation.

    Dense arrays, pandas data frames, and SciPy sparse matrices are accepted.
    Counts must be finite and non-negative.  Aggregates with a zero total
    library size cannot be CPM-normalized and are excluded.  At least two
    non-zero donor libraries are required in each condition.

    Notes
    -----
    This transparent Welch baseline is suitable for the project's independent
    verification lesson.  For a production study, use an established
    count-aware model (for example edgeR or DESeq2) with the full study design.
    """

    frame = _validate_obs(
        obs,
        required=[subtype_key, condition_key, donor_key],
        condition_a=condition_a,
        condition_b=condition_b,
    )
    genes = _validate_gene_names(gene_names)
    matrix = _validate_matrix(
        counts,
        n_rows=len(frame),
        n_columns=len(genes),
        name="counts",
        require_nonnegative=True,
    )

    selected = (
        frame[subtype_key].eq(headline_subtype)
        & frame[condition_key].isin([condition_a, condition_b])
        & frame[donor_key].notna()
    ).to_numpy(dtype=bool)
    selected_positions = np.flatnonzero(selected)

    if selected_positions.size == 0:
        return _untestable_pseudobulk_result(
            genes, headline_subtype, condition_a, condition_b, 0, 0, 0
        )

    metadata = frame.iloc[selected_positions][[condition_key, donor_key]].reset_index(drop=True)
    group_index = pd.MultiIndex.from_frame(metadata[[condition_key, donor_key]])
    group_codes, unique_groups = pd.factorize(group_index, sort=False)
    number_groups = len(unique_groups)

    membership = sparse.csr_matrix(
        (
            np.ones(selected_positions.size, dtype=float),
            (group_codes, np.arange(selected_positions.size, dtype=np.int64)),
        ),
        shape=(number_groups, selected_positions.size),
    )
    selected_counts = matrix[selected_positions]
    aggregate = membership @ selected_counts
    if sparse.issparse(aggregate):
        aggregate_array = aggregate.toarray()
    else:
        aggregate_array = np.asarray(aggregate, dtype=float)

    group_metadata = (
        metadata.assign(__group=group_codes)
        .drop_duplicates("__group")
        .sort_values("__group")
        .reset_index(drop=True)
    )
    library_sizes = aggregate_array.sum(axis=1)
    usable = np.isfinite(library_sizes) & (library_sizes > 0.0)
    zero_library_count = int((~usable).sum())
    aggregate_array = aggregate_array[usable]
    group_metadata = group_metadata.loc[usable].reset_index(drop=True)
    library_sizes = library_sizes[usable]

    conditions = group_metadata[condition_key].to_numpy()
    is_a = conditions == condition_a
    is_b = conditions == condition_b
    number_a = int(is_a.sum())
    number_b = int(is_b.sum())

    if aggregate_array.shape[0] == 0:
        return _untestable_pseudobulk_result(
            genes,
            headline_subtype,
            condition_a,
            condition_b,
            number_a,
            number_b,
            zero_library_count,
        )

    cpm = aggregate_array / library_sizes[:, np.newaxis] * 1_000_000.0
    log2_cpm = np.log2(cpm + 1.0)

    rows: list[dict[str, Any]] = []
    for gene_position, gene in enumerate(genes):
        values_a = log2_cpm[is_a, gene_position]
        values_b = log2_cpm[is_b, gene_position]
        statistic, p_value = _welch_test(values_a, values_b)
        mean_a = _safe_mean(values_a)
        mean_b = _safe_mean(values_b)
        rows.append(
            {
                "gene": gene,
                "headline_subtype": headline_subtype,
                "condition_a": condition_a,
                "condition_b": condition_b,
                "mean_log2_cpm_a": mean_a,
                "mean_log2_cpm_b": mean_b,
                "log2fc": (
                    mean_b - mean_a if np.isfinite(mean_a) and np.isfinite(mean_b) else np.nan
                ),
                "t_statistic": statistic,
                "p_value": p_value,
                "n_donors_a": number_a,
                "n_donors_b": number_b,
                "zero_library_aggregates_excluded": zero_library_count,
            }
        )

    result = pd.DataFrame(rows)
    result["p_adj"] = benjamini_hochberg(result["p_value"].to_numpy(dtype=float))
    result["significant"] = result["p_adj"].lt(_FDR_THRESHOLD).fillna(False)
    result["test_status"] = _test_status(result["p_adj"])
    return result


def per_cell_de(
    expression: Any,
    obs: pd.DataFrame,
    gene_names: Sequence[Any],
    subtype_key: str,
    headline_subtype: Any,
    condition_key: str,
    condition_a: Any,
    condition_b: Any,
) -> pd.DataFrame:
    """Run exploratory cell-level Mann-Whitney differential expression.

    The input is expected to be normalized log2-scale expression.  Therefore
    ``log2fc`` is reported as the difference in mean expression (condition B
    minus condition A).  The Mann-Whitney U statistic is also oriented with B
    as the first group, and ``rank_biserial`` ranges from -1 to 1.

    This analysis treats cells as independent and is consequently susceptible
    to pseudoreplication.  The output marks every row as exploratory and must
    be passed through :func:`pseudobulk_de` before a final claim is made.
    Dense and SciPy sparse matrices are supported.
    """

    frame = _validate_obs(
        obs,
        required=[subtype_key, condition_key],
        condition_a=condition_a,
        condition_b=condition_b,
    )
    genes = _validate_gene_names(gene_names)
    matrix = _validate_matrix(
        expression,
        n_rows=len(frame),
        n_columns=len(genes),
        name="expression",
        require_nonnegative=False,
    )

    selected = (
        frame[subtype_key].eq(headline_subtype)
        & frame[condition_key].isin([condition_a, condition_b])
    ).to_numpy(dtype=bool)
    selected_positions = np.flatnonzero(selected)
    selected_conditions = frame.iloc[selected_positions][condition_key].to_numpy()
    is_a = selected_conditions == condition_a
    is_b = selected_conditions == condition_b
    number_a = int(is_a.sum())
    number_b = int(is_b.sum())

    selected_matrix = matrix[selected_positions]
    rows: list[dict[str, Any]] = []
    for gene_position, gene in enumerate(genes):
        values = _matrix_column(selected_matrix, gene_position)
        values_a = values[is_a]
        values_b = values[is_b]
        mean_a = _safe_mean(values_a)
        mean_b = _safe_mean(values_b)

        if values_a.size == 0 or values_b.size == 0:
            statistic = np.nan
            p_value = np.nan
            rank_biserial = np.nan
        elif np.all(values == values[0]):
            # Recent SciPy versions may raise for a completely tied sample.
            # The exact null result is unambiguous: no rank separation.
            statistic = float(values_b.size * values_a.size / 2.0)
            p_value = 1.0
            rank_biserial = 0.0
        else:
            try:
                test = stats.mannwhitneyu(
                    values_b,
                    values_a,
                    alternative="two-sided",
                    method="auto",
                )
                statistic = float(test.statistic)
                p_value = float(test.pvalue)
                rank_biserial = float(2.0 * statistic / (values_b.size * values_a.size) - 1.0)
            except ValueError:
                statistic = np.nan
                p_value = np.nan
                rank_biserial = np.nan

        rows.append(
            {
                "gene": gene,
                "headline_subtype": headline_subtype,
                "condition_a": condition_a,
                "condition_b": condition_b,
                "mean_expression_a": mean_a,
                "mean_expression_b": mean_b,
                "log2fc": (
                    mean_b - mean_a if np.isfinite(mean_a) and np.isfinite(mean_b) else np.nan
                ),
                "u_statistic": statistic,
                "rank_biserial": rank_biserial,
                "p_value": p_value,
                "n_cells_a": number_a,
                "n_cells_b": number_b,
                "exploratory": True,
                "analysis_unit": "cell (not an independent biological replicate)",
            }
        )

    result = pd.DataFrame(rows)
    result["p_adj"] = benjamini_hochberg(result["p_value"].to_numpy(dtype=float))
    result["significant"] = result["p_adj"].lt(_FDR_THRESHOLD).fillna(False)
    result["test_status"] = _test_status(result["p_adj"])
    return result


def build_reviewer_table(
    per_cell: pd.DataFrame,
    pseudobulk: pd.DataFrame,
    evidence: Any = None,
    top_n: int = 30,
) -> pd.DataFrame:
    """Audit top per-cell hits against pseudobulk and external evidence.

    Genes are ranked by per-cell adjusted p-value (then absolute effect size)
    and the first ``top_n`` unique genes are audited.  Donor-level status is:

    ``SURVIVES``
        Pseudobulk FDR is below 0.05 and its non-zero effect has the same sign.
    ``DOES_NOT_SURVIVE``
        A donor test exists, but its FDR is not below 0.05 (or either effect is
        exactly zero).
    ``DIRECTION_REVERSES``
        The per-cell and pseudobulk effects have opposite signs.
    ``NOT_TESTABLE``
        A pseudobulk adjusted p-value or either effect is unavailable.

    ``final_status`` is ``VERIFIED`` only when donor status is ``SURVIVES``
    *and* supplied evidence explicitly passes.  Missing evidence, a citation
    without a pass flag, or any failed check produces ``NOT_VERIFIED``.

    Evidence may be a data frame keyed by ``gene`` (or ``symbol``), a Series
    keyed by gene, or a mapping.  A combined column such as ``evidence_pass``
    or ``passes`` is accepted.  Alternatively, both ``literature_pass`` and
    ``target_pass`` must be present and pass.  Citations and other evidence
    columns are retained with an ``evidence_`` prefix.
    """

    if not isinstance(per_cell, pd.DataFrame):
        raise TypeError("per_cell must be a pandas DataFrame")
    if not isinstance(pseudobulk, pd.DataFrame):
        raise TypeError("pseudobulk must be a pandas DataFrame")
    if isinstance(top_n, bool) or not isinstance(top_n, int | np.integer) or top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    per_cell_gene = _find_column(per_cell, ["gene", "gene_name", "symbol"], "per_cell gene")
    per_cell_effect = _find_column(
        per_cell,
        ["log2fc", "log2_fold_change", "log2FoldChange", "effect", "delta"],
        "per_cell effect",
    )
    per_cell_p = _find_optional_column(per_cell, ["p_value", "pvalue", "pval", "p"])
    per_cell_fdr = _find_optional_column(
        per_cell, ["p_adj", "padj", "p_adjusted", "fdr", "q_value", "qvalue"]
    )
    if per_cell_p is None and per_cell_fdr is None:
        raise KeyError("per_cell must contain a raw or adjusted p-value column")

    pc = pd.DataFrame(
        {
            "gene": per_cell[per_cell_gene],
            "per_cell_log2fc": pd.to_numeric(per_cell[per_cell_effect], errors="coerce"),
            "per_cell_p_value": (
                pd.to_numeric(per_cell[per_cell_p], errors="coerce")
                if per_cell_p is not None
                else np.nan
            ),
            "per_cell_p_adj": (
                pd.to_numeric(per_cell[per_cell_fdr], errors="coerce")
                if per_cell_fdr is not None
                else np.nan
            ),
        }
    )
    pc = pc.loc[pc["gene"].notna()].copy()
    pc["__rank_p"] = pc["per_cell_p_adj"].where(
        pc["per_cell_p_adj"].notna(), pc["per_cell_p_value"]
    )
    pc["__absolute_effect"] = pc["per_cell_log2fc"].abs()
    pc["__gene_sort"] = pc["gene"].astype(str)
    pc = pc.sort_values(
        ["__rank_p", "__absolute_effect", "__gene_sort"],
        ascending=[True, False, True],
        na_position="last",
        kind="mergesort",
    )
    pc = pc.drop_duplicates("gene", keep="first").head(int(top_n)).copy()
    pc["per_cell_rank"] = np.arange(1, len(pc) + 1, dtype=np.int64)
    pc = pc.drop(columns=["__rank_p", "__absolute_effect", "__gene_sort"])

    pseudobulk_gene = _find_column(pseudobulk, ["gene", "gene_name", "symbol"], "pseudobulk gene")
    pseudobulk_effect = _find_optional_column(
        pseudobulk,
        ["log2fc", "log2_fold_change", "log2FoldChange", "effect", "delta"],
    )
    pseudobulk_p = _find_optional_column(pseudobulk, ["p_value", "pvalue", "pval", "p"])
    pseudobulk_fdr = _find_optional_column(
        pseudobulk, ["p_adj", "padj", "p_adjusted", "fdr", "q_value", "qvalue"]
    )

    pb = pd.DataFrame({"gene": pseudobulk[pseudobulk_gene]})
    pb["pseudobulk_log2fc"] = (
        pd.to_numeric(pseudobulk[pseudobulk_effect], errors="coerce")
        if pseudobulk_effect is not None
        else np.nan
    )
    pb["pseudobulk_p_value"] = (
        pd.to_numeric(pseudobulk[pseudobulk_p], errors="coerce")
        if pseudobulk_p is not None
        else np.nan
    )
    pb["pseudobulk_p_adj"] = (
        pd.to_numeric(pseudobulk[pseudobulk_fdr], errors="coerce")
        if pseudobulk_fdr is not None
        else np.nan
    )
    pb = pb.loc[pb["gene"].notna()].copy()
    if pb["gene"].duplicated().any():
        duplicates = pb.loc[pb["gene"].duplicated(keep=False), "gene"].astype(str).unique()
        raise ValueError(f"pseudobulk contains duplicate genes: {', '.join(duplicates)}")

    reviewer = pc.merge(pb, on="gene", how="left", validate="one_to_one", sort=False)
    reviewer["matching_direction"] = (
        reviewer["per_cell_log2fc"] * reviewer["pseudobulk_log2fc"] > 0.0
    )

    testable = (
        np.isfinite(reviewer["per_cell_log2fc"])
        & np.isfinite(reviewer["pseudobulk_log2fc"])
        & np.isfinite(reviewer["pseudobulk_p_adj"])
    )
    reverses = testable & (reviewer["per_cell_log2fc"] * reviewer["pseudobulk_log2fc"] < 0.0)
    survives = (
        testable & reviewer["matching_direction"] & reviewer["pseudobulk_p_adj"].lt(_FDR_THRESHOLD)
    )
    reviewer["status"] = np.select(
        [~testable, reverses, survives],
        ["NOT_TESTABLE", "DIRECTION_REVERSES", "SURVIVES"],
        default="DOES_NOT_SURVIVE",
    )
    reviewer["donor_status"] = reviewer["status"]

    per_cell_for_delta = reviewer["per_cell_p_adj"].where(
        reviewer["per_cell_p_adj"].notna(), reviewer["per_cell_p_value"]
    )
    pseudobulk_for_delta = reviewer["pseudobulk_p_adj"]
    valid_delta = (
        np.isfinite(per_cell_for_delta)
        & np.isfinite(pseudobulk_for_delta)
        & per_cell_for_delta.ge(0.0)
        & pseudobulk_for_delta.ge(0.0)
    )
    reviewer["pseudoreplication_delta_log10"] = np.nan
    smallest = np.finfo(float).tiny
    reviewer.loc[valid_delta, "pseudoreplication_delta_log10"] = np.log10(
        np.clip(pseudobulk_for_delta[valid_delta].to_numpy(dtype=float), smallest, 1.0)
    ) - np.log10(np.clip(per_cell_for_delta[valid_delta].to_numpy(dtype=float), smallest, 1.0))

    evidence_frame = _normalise_evidence(evidence)
    if evidence_frame.empty:
        reviewer["evidence_pass"] = False
    else:
        reviewer = reviewer.merge(
            evidence_frame,
            on="gene",
            how="left",
            validate="one_to_one",
            sort=False,
        )
        reviewer["evidence_pass"] = reviewer["evidence_pass"].eq(True).fillna(False)

    reviewer["verified"] = reviewer["status"].eq("SURVIVES") & reviewer["evidence_pass"]
    reviewer["final_status"] = np.where(reviewer["verified"], "VERIFIED", "NOT_VERIFIED")
    reviewer = reviewer.sort_values("per_cell_rank", kind="mergesort").reset_index(drop=True)

    leading_columns = [
        "gene",
        "per_cell_rank",
        "per_cell_log2fc",
        "per_cell_p_value",
        "per_cell_p_adj",
        "pseudobulk_log2fc",
        "pseudobulk_p_value",
        "pseudobulk_p_adj",
        "pseudoreplication_delta_log10",
        "matching_direction",
        "status",
        "donor_status",
        "evidence_pass",
        "verified",
        "final_status",
    ]
    trailing_columns = [column for column in reviewer.columns if column not in leading_columns]
    return reviewer[leading_columns + trailing_columns]


def _validate_obs(
    obs: pd.DataFrame,
    required: Sequence[str],
    condition_a: Any,
    condition_b: Any,
) -> pd.DataFrame:
    """Validate shared observation metadata without mutating the caller."""

    if not isinstance(obs, pd.DataFrame):
        raise TypeError("obs must be a pandas DataFrame")
    missing = [column for column in required if column not in obs.columns]
    if missing:
        raise KeyError(f"obs is missing required columns: {', '.join(missing)}")
    try:
        same_condition = bool(condition_a == condition_b)
    except (TypeError, ValueError):
        same_condition = False
    if same_condition:
        raise ValueError("condition_a and condition_b must be different")
    return obs


def _validate_gene_names(gene_names: Sequence[Any]) -> list[Any]:
    """Return validated, unique gene identifiers."""

    if isinstance(gene_names, str | bytes):
        raise TypeError("gene_names must be a sequence, not one string")
    try:
        genes = list(gene_names)
    except TypeError as exc:
        raise TypeError("gene_names must be a one-dimensional sequence") from exc
    if any(pd.isna(gene) for gene in genes):
        raise ValueError("gene_names cannot contain missing values")
    if pd.Index(genes).duplicated().any():
        duplicates = pd.Index(genes)[pd.Index(genes).duplicated()].astype(str).unique()
        raise ValueError(f"gene_names contains duplicates: {', '.join(duplicates)}")
    return genes


def _validate_matrix(
    matrix: Any,
    n_rows: int,
    n_columns: int,
    name: str,
    require_nonnegative: bool,
) -> np.ndarray | sparse.csr_matrix:
    """Validate a two-dimensional dense or sparse numeric matrix."""

    if sparse.issparse(matrix):
        if matrix.ndim != 2:
            raise ValueError(f"{name} must be two-dimensional")
        checked: np.ndarray | sparse.csr_matrix = matrix.tocsr().astype(float, copy=False)
        shape = checked.shape
        stored_values = checked.data
        if np.any(~np.isfinite(stored_values)):
            raise ValueError(f"{name} must contain only finite values")
        if require_nonnegative and np.any(stored_values < 0.0):
            raise ValueError(f"{name} must contain non-negative raw counts")
    else:
        source = matrix.to_numpy() if isinstance(matrix, pd.DataFrame) else matrix
        if np.iscomplexobj(source):
            raise ValueError(f"{name} must contain real-valued data")
        try:
            checked = np.asarray(source, dtype=float)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{name} must be numeric") from exc
        if checked.ndim != 2:
            raise ValueError(f"{name} must be two-dimensional")
        shape = checked.shape
        if np.any(~np.isfinite(checked)):
            raise ValueError(f"{name} must contain only finite values")
        if require_nonnegative and np.any(checked < 0.0):
            raise ValueError(f"{name} must contain non-negative raw counts")

    expected = (n_rows, n_columns)
    if shape != expected:
        raise ValueError(f"{name} has shape {shape}; expected {expected}")
    return checked


def _matrix_column(matrix: np.ndarray | sparse.spmatrix, position: int) -> np.ndarray:
    """Extract one dense column from either supported matrix representation."""

    if sparse.issparse(matrix):
        return matrix.getcol(position).toarray().ravel()
    return np.asarray(matrix[:, position], dtype=float).ravel()


def _welch_test(values_a: np.ndarray, values_b: np.ndarray) -> tuple[float, float]:
    """Return a deterministic Welch statistic and p-value, oriented B minus A."""

    clean_a = np.asarray(values_a, dtype=float)
    clean_b = np.asarray(values_b, dtype=float)
    clean_a = clean_a[np.isfinite(clean_a)]
    clean_b = clean_b[np.isfinite(clean_b)]
    if clean_a.size < 2 or clean_b.size < 2:
        return np.nan, np.nan

    mean_a = float(clean_a.mean())
    mean_b = float(clean_b.mean())
    variance_a = float(clean_a.var(ddof=1))
    variance_b = float(clean_b.var(ddof=1))
    variance_term_a = variance_a / clean_a.size
    variance_term_b = variance_b / clean_b.size
    standard_error_squared = variance_term_a + variance_term_b

    if standard_error_squared == 0.0:
        difference = mean_b - mean_a
        if difference == 0.0:
            return 0.0, 1.0
        return float(np.copysign(np.inf, difference)), 0.0

    statistic = (mean_b - mean_a) / np.sqrt(standard_error_squared)
    denominator = variance_term_a**2 / (clean_a.size - 1) + variance_term_b**2 / (clean_b.size - 1)
    if denominator == 0.0:
        degrees_of_freedom = np.inf
    else:
        degrees_of_freedom = standard_error_squared**2 / denominator
    p_value = 2.0 * stats.t.sf(abs(statistic), degrees_of_freedom)
    return float(statistic), float(np.clip(p_value, 0.0, 1.0))


def _safe_mean(values: np.ndarray) -> float:
    """Return a finite-array mean or NaN for an empty array."""

    return float(np.mean(values)) if values.size else np.nan


def _test_status(adjusted_pvalues: pd.Series) -> np.ndarray:
    """Map adjusted p-values to concise testability labels."""

    values = pd.to_numeric(adjusted_pvalues, errors="coerce")
    return np.select(
        [values.isna(), values.lt(_FDR_THRESHOLD)],
        ["NOT_TESTABLE", "SIGNIFICANT"],
        default="NOT_SIGNIFICANT",
    )


def _empty_module_result() -> pd.DataFrame:
    """Create a schema-stable empty module-score result."""

    return pd.DataFrame(
        columns=[
            "subtype",
            "condition_a",
            "condition_b",
            "mean_a",
            "mean_b",
            "delta",
            "n_units_a",
            "n_units_b",
            "n_donors_a",
            "n_donors_b",
            "t_statistic",
            "p_value",
            "donor_aware",
            "analysis_unit",
            "p_adj",
            "significant",
            "test_status",
        ]
    )


def _untestable_pseudobulk_result(
    genes: Sequence[Any],
    headline_subtype: Any,
    condition_a: Any,
    condition_b: Any,
    number_a: int,
    number_b: int,
    zero_library_count: int,
) -> pd.DataFrame:
    """Create one explicitly untestable pseudobulk row per requested gene."""

    number_genes = len(genes)
    return pd.DataFrame(
        {
            "gene": list(genes),
            "headline_subtype": [headline_subtype] * number_genes,
            "condition_a": [condition_a] * number_genes,
            "condition_b": [condition_b] * number_genes,
            "mean_log2_cpm_a": np.full(number_genes, np.nan),
            "mean_log2_cpm_b": np.full(number_genes, np.nan),
            "log2fc": np.full(number_genes, np.nan),
            "t_statistic": np.full(number_genes, np.nan),
            "p_value": np.full(number_genes, np.nan),
            "n_donors_a": np.full(number_genes, number_a, dtype=int),
            "n_donors_b": np.full(number_genes, number_b, dtype=int),
            "zero_library_aggregates_excluded": np.full(
                number_genes, zero_library_count, dtype=int
            ),
            "p_adj": np.full(number_genes, np.nan),
            "significant": np.full(number_genes, False),
            "test_status": np.full(number_genes, "NOT_TESTABLE", dtype=object),
        }
    )


def _find_optional_column(frame: pd.DataFrame, candidates: Sequence[str]) -> str | None:
    """Return the first matching column name, allowing case-insensitive matches."""

    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    lower_to_original = {str(column).lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    return None


def _find_column(frame: pd.DataFrame, candidates: Sequence[str], description: str) -> str:
    """Return a required column or raise an actionable error."""

    column = _find_optional_column(frame, candidates)
    if column is None:
        raise KeyError(f"missing {description} column; expected one of {', '.join(candidates)}")
    return column


def _normalise_evidence(evidence: Any) -> pd.DataFrame:
    """Normalize supported evidence containers and derive a strict pass flag."""

    if evidence is None:
        return pd.DataFrame(columns=["gene", "evidence_pass"])
    if isinstance(evidence, pd.DataFrame):
        evidence_data = evidence.copy()
    elif isinstance(evidence, pd.Series):
        evidence_data = pd.DataFrame(
            {"gene": evidence.index.to_list(), "evidence_pass": evidence.to_list()}
        )
    elif isinstance(evidence, Mapping):
        records: list[dict[str, Any]] = []
        for gene, value in evidence.items():
            if isinstance(value, Mapping):
                record = {"gene": gene, **dict(value)}
            else:
                record = {"gene": gene, "evidence_pass": value}
            records.append(record)
        evidence_data = pd.DataFrame(records)
    else:
        raise TypeError("evidence must be a DataFrame, Series, mapping, or None")

    if evidence_data.empty:
        return pd.DataFrame(columns=["gene", "evidence_pass"])

    gene_column = _find_optional_column(evidence_data, ["gene", "gene_name", "symbol"])
    if gene_column is None:
        raise KeyError("evidence must contain a gene or symbol column")
    if gene_column != "gene":
        evidence_data = evidence_data.rename(columns={gene_column: "gene"})
    evidence_data = evidence_data.loc[evidence_data["gene"].notna()].copy()
    if evidence_data["gene"].duplicated().any():
        duplicates = (
            evidence_data.loc[evidence_data["gene"].duplicated(keep=False), "gene"]
            .astype(str)
            .unique()
        )
        raise ValueError(f"evidence contains duplicate genes: {', '.join(duplicates)}")

    combined_pass = _find_optional_column(
        evidence_data,
        [
            "evidence_pass",
            "passes",
            "passed",
            "plausibility_pass",
            "evidence_status",
            "status",
        ],
    )
    literature_pass = _find_optional_column(
        evidence_data, ["literature_pass", "pubmed_pass", "literature_status"]
    )
    target_pass = _find_optional_column(
        evidence_data, ["target_pass", "open_targets_pass", "target_status"]
    )

    if combined_pass is not None:
        explicit_pass = evidence_data[combined_pass].map(_explicitly_passes)
    elif literature_pass is not None and target_pass is not None:
        explicit_pass = evidence_data[literature_pass].map(_explicitly_passes) & evidence_data[
            target_pass
        ].map(_explicitly_passes)
    else:
        explicit_pass = pd.Series(False, index=evidence_data.index, dtype=bool)

    columns_to_keep = [column for column in evidence_data.columns if column != "gene"]
    rename: dict[Any, str] = {}
    for column in columns_to_keep:
        if column == "evidence_pass":
            continue
        target_name = str(column)
        if not target_name.startswith("evidence_"):
            target_name = f"evidence_{target_name}"
        rename[column] = target_name
    evidence_data = evidence_data.rename(columns=rename)
    # Overwrite any permissively typed source flag with the normalized boolean.
    evidence_data["evidence_pass"] = explicit_pass.to_numpy(dtype=bool)

    ordered = ["gene", "evidence_pass"] + [
        column for column in evidence_data.columns if column not in {"gene", "evidence_pass"}
    ]
    return evidence_data[ordered]


def _explicitly_passes(value: Any) -> bool:
    """Return True only for an unambiguous positive evidence value."""

    if isinstance(value, bool | np.bool_):
        return bool(value)
    if isinstance(value, int | np.integer) and not isinstance(value, bool):
        return int(value) == 1
    if isinstance(value, str):
        return value.strip().casefold() in {
            "pass",
            "passed",
            "true",
            "yes",
            "verified",
            "supported",
            "plausible",
        }
    return False


__all__ = [
    "benjamini_hochberg",
    "build_reviewer_table",
    "donor_module_statistics",
    "per_cell_de",
    "pseudobulk_de",
]
