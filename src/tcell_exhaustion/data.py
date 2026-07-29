"""Input loading, validation, and honest analysis-branch selection.

This module intentionally does not repair inputs.  It never rounds expression
values into counts, guesses metadata columns, remaps condition labels, or uses
``adata.X`` when the configured raw-count layer is absent.  Those conveniences
would make the downstream result impossible to audit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from tcell_exhaustion.config import AnalysisConfig


class DataValidationError(ValueError):
    """Raised when input evidence cannot satisfy a declared requirement."""


class AnalysisBranch(StrEnum):
    """The four pre-declared paths available after the input audit."""

    DONOR_AWARE = "donor_aware"
    EXPLORATORY_NO_DONOR = "exploratory_no_donor"
    MARKER_FALLBACK = "marker_fallback"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class InputAudit:
    """A serialisable record of what was observed and why a branch was chosen."""

    branch: AnalysisBranch
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    n_cells: int = 0
    n_genes: int = 0
    condition_counts: Mapping[str, int] = field(default_factory=dict)
    donors_per_condition: Mapping[str, int] = field(default_factory=dict)
    missing_genes: tuple[str, ...] = ()
    counts_layer: str = "counts"
    raw_counts_valid: bool = False

    @property
    def decision(self) -> str:
        """Plain-string alias convenient for reports and YAML/JSON output."""

        return self.branch.value

    @property
    def blocked(self) -> bool:
        return self.branch is AnalysisBranch.BLOCKED

    @property
    def reviewer_enabled(self) -> bool:
        """Whether donor-level pseudobulk verification is in scope."""

        return self.branch is AnalysisBranch.DONOR_AWARE

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly audit record."""

        return {
            "branch": self.branch.value,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "n_cells": self.n_cells,
            "n_genes": self.n_genes,
            "condition_counts": dict(self.condition_counts),
            "donors_per_condition": dict(self.donors_per_condition),
            "missing_genes": list(self.missing_genes),
            "counts_layer": self.counts_layer,
            "raw_counts_valid": self.raw_counts_valid,
        }


def load_h5ad(path: str | Path, *, backed: str | None = None) -> ad.AnnData:
    """Load an AnnData ``.h5ad`` file without altering it."""

    input_path = Path(path)
    if input_path.suffix.lower() != ".h5ad":
        raise DataValidationError(f"Expected a .h5ad input, got: {input_path}")
    if not input_path.is_file():
        raise DataValidationError(f"Input file does not exist: {input_path}")
    try:
        return ad.read_h5ad(input_path, backed=backed)
    except (OSError, ValueError, TypeError) as exc:
        raise DataValidationError(f"Could not read {input_path}: {exc}") from exc


# Descriptive alias used by some callers.
load_adata = load_h5ad


def get_raw_counts(
    adata: ad.AnnData,
    layer: str = "counts",
    *,
    validate: bool = True,
) -> Any:
    """Return the explicitly configured raw-count matrix.

    There is deliberately no fallback to ``adata.X`` or ``adata.raw.X``.  A
    missing provenance-bearing layer is an audit failure, not permission to
    guess which matrix contains counts.
    """

    if layer not in adata.layers:
        raise DataValidationError(
            f"Raw-count layer {layer!r} is missing; available layers: {list(adata.layers.keys())}"
        )
    counts = adata.layers[layer]
    if tuple(counts.shape) != tuple(adata.shape):
        raise DataValidationError(
            f"Raw-count layer {layer!r} has shape {counts.shape}, expected {adata.shape}"
        )
    if validate:
        validate_raw_counts(counts)
    return counts


# Backwards/readability aliases.
extract_raw_counts = get_raw_counts
retrieve_raw_counts = get_raw_counts


def validate_raw_counts(counts: Any, *, atol: float = 1e-8) -> None:
    """Require a finite, non-negative, integer-valued two-dimensional matrix."""

    if not hasattr(counts, "shape") or len(counts.shape) != 2:
        raise DataValidationError("Raw counts must be a two-dimensional matrix")
    values = counts.data if sparse.issparse(counts) else np.asarray(counts)
    if values.dtype == np.dtype("bool") or not np.issubdtype(values.dtype, np.number):
        raise DataValidationError("Raw counts must have a numeric, non-boolean dtype")
    if np.iscomplexobj(values):
        raise DataValidationError("Raw counts must be real-valued")
    if values.size == 0:
        return
    if not np.isfinite(values).all():
        raise DataValidationError("Raw counts contain NaN or infinite values")
    if np.any(values < 0):
        raise DataValidationError("Raw counts contain negative values")
    if not np.issubdtype(values.dtype, np.integer):
        nearest = np.rint(values)
        if not np.allclose(values, nearest, rtol=0.0, atol=atol):
            raise DataValidationError("Raw counts contain non-integer values")


def required_genes(config: AnalysisConfig, *, include_markers: bool = True) -> tuple[str, ...]:
    """Return the unique, ordered genes needed by the declared analysis."""

    genes: list[str] = ["CD8A", "CD8B", "CD4", *config.exhaustion_genes]
    if include_markers:
        for panel in config.marker_panels.as_dict().values():
            genes.extend(panel)
        genes.extend(config.effector_memory_rule.positive)
        genes.extend(config.effector_memory_rule.negative)
    return tuple(dict.fromkeys(genes))


def missing_required_genes(
    adata: ad.AnnData,
    config: AnalysisConfig,
    *,
    include_markers: bool = True,
) -> tuple[str, ...]:
    """List required symbols absent from ``adata.var_names``."""

    observed = set(map(str, adata.var_names))
    return tuple(
        gene
        for gene in required_genes(config, include_markers=include_markers)
        if gene not in observed
    )


def validate_genes(
    adata: ad.AnnData,
    config: AnalysisConfig,
    *,
    include_markers: bool = True,
) -> tuple[str, ...]:
    """Validate unique gene symbols and return the required ordered panel."""

    if not adata.var_names.is_unique:
        duplicates = pd.Index(adata.var_names)[pd.Index(adata.var_names).duplicated()].unique()
        preview = ", ".join(map(str, duplicates[:5]))
        raise DataValidationError(f"adata.var_names contains duplicate gene symbols: {preview}")
    missing = missing_required_genes(adata, config, include_markers=include_markers)
    if missing:
        raise DataValidationError(
            "Required gene symbols are missing from adata.var_names: " + ", ".join(missing)
        )
    return required_genes(config, include_markers=include_markers)


def validate_metadata(adata: ad.AnnData, config: AnalysisConfig) -> dict[str, int]:
    """Validate the condition column and return its observed value counts.

    Donor metadata is optional at this stage because its absence selects the
    exploratory branch.  The configured condition column is not optional:
    without it, the pipeline cannot distinguish an intentional one-condition
    fallback from missing metadata.
    """

    if config.condition_key not in adata.obs:
        raise DataValidationError(
            f"Condition column {config.condition_key!r} is missing from adata.obs"
        )
    condition_values = _clean_labels(adata.obs[config.condition_key])
    if condition_values.empty:
        raise DataValidationError(
            f"Condition column {config.condition_key!r} contains no non-missing labels"
        )
    return {str(key): int(value) for key, value in condition_values.value_counts().items()}


def audit_input(adata: ad.AnnData, config: AnalysisConfig) -> InputAudit:
    """Validate input evidence and commit to one pre-declared analysis branch."""

    errors: list[str] = []
    warnings: list[str] = []
    condition_counts: dict[str, int] = {}
    donors_per_condition: dict[str, int] = {}
    missing: tuple[str, ...] = ()
    raw_counts_valid = False

    if adata.n_obs == 0:
        errors.append("The dataset contains no cells")
    if adata.n_vars == 0:
        errors.append("The dataset contains no genes")

    try:
        get_raw_counts(adata, config.counts_layer, validate=True)
        raw_counts_valid = True
    except DataValidationError as exc:
        errors.append(str(exc))

    if not adata.var_names.is_unique:
        errors.append("adata.var_names contains duplicate gene symbols")
    missing = missing_required_genes(adata, config)
    if missing:
        errors.append("Required gene symbols are missing: " + ", ".join(missing))

    try:
        condition_counts = validate_metadata(adata, config)
    except DataValidationError as exc:
        errors.append(str(exc))

    if errors:
        return InputAudit(
            branch=AnalysisBranch.BLOCKED,
            reasons=tuple(errors),
            warnings=tuple(warnings),
            n_cells=int(adata.n_obs),
            n_genes=int(adata.n_vars),
            condition_counts=condition_counts,
            donors_per_condition=donors_per_condition,
            missing_genes=missing,
            counts_layer=config.counts_layer,
            raw_counts_valid=raw_counts_valid,
        )

    observed = set(condition_counts)
    expected = {str(config.condition_a), str(config.condition_b)}
    if len(observed) == 1:
        only_label = next(iter(observed))
        return InputAudit(
            branch=AnalysisBranch.MARKER_FALLBACK,
            reasons=(
                f"Only one condition ({only_label!r}) is present; report pre-registered "
                "marker-defined subtype patterns descriptively. A marker-defined exhaustion "
                "contrast would be circular without an independent grouping variable.",
            ),
            warnings=("A directional condition-B versus condition-A claim is out of scope.",),
            n_cells=int(adata.n_obs),
            n_genes=int(adata.n_vars),
            condition_counts=condition_counts,
            counts_layer=config.counts_layer,
            raw_counts_valid=True,
        )

    missing_conditions = expected.difference(observed)
    if missing_conditions:
        return InputAudit(
            branch=AnalysisBranch.BLOCKED,
            reasons=(
                "Configured contrast labels are not both present. Missing: "
                + ", ".join(sorted(missing_conditions))
                + ". Labels are not remapped automatically.",
            ),
            n_cells=int(adata.n_obs),
            n_genes=int(adata.n_vars),
            condition_counts=condition_counts,
            counts_layer=config.counts_layer,
            raw_counts_valid=True,
        )

    extras = observed.difference(expected)
    if extras:
        warnings.append(
            "Additional condition labels will be excluded from the configured A/B contrast: "
            + ", ".join(sorted(extras))
        )

    if config.donor_key not in adata.obs:
        return _exploratory_audit(
            adata,
            config,
            condition_counts,
            warnings,
            reason=f"Donor column {config.donor_key!r} is absent.",
        )

    conditions = _clean_labels(adata.obs[config.condition_key])
    donors = _clean_labels(adata.obs[config.donor_key])
    contrast_mask = conditions.isin(expected)
    missing_donor_mask = contrast_mask & donors.isna()
    if bool(missing_donor_mask.any()):
        return _exploratory_audit(
            adata,
            config,
            condition_counts,
            warnings,
            reason=(
                f"Donor column {config.donor_key!r} is missing for "
                f"{int(missing_donor_mask.sum())} A/B cells."
            ),
        )

    metadata = pd.DataFrame({"condition": conditions, "donor": donors})
    metadata = metadata.loc[contrast_mask]
    donors_per_condition = {
        label: int(metadata.loc[metadata["condition"] == label, "donor"].nunique())
        for label in (str(config.condition_a), str(config.condition_b))
    }
    insufficient = {
        label: count
        for label, count in donors_per_condition.items()
        if count < config.min_donors_per_condition
    }
    if insufficient:
        detail = ", ".join(f"{label}={count}" for label, count in insufficient.items())
        return _exploratory_audit(
            adata,
            config,
            condition_counts,
            warnings,
            reason=(
                "Too few independent donors for the donor-aware path "
                f"({detail}; require >= {config.min_donors_per_condition} per condition)."
            ),
            donors_per_condition=donors_per_condition,
        )

    return InputAudit(
        branch=AnalysisBranch.DONOR_AWARE,
        reasons=(
            "Both configured conditions and sufficient donor replicates are present; "
            "donor-level pseudobulk is the primary statistical path.",
        ),
        warnings=tuple(warnings),
        n_cells=int(adata.n_obs),
        n_genes=int(adata.n_vars),
        condition_counts=condition_counts,
        donors_per_condition=donors_per_condition,
        counts_layer=config.counts_layer,
        raw_counts_valid=True,
    )


# Public aliases that read naturally at call sites.
validate_input = audit_input
decide_analysis_branch = audit_input


def _exploratory_audit(
    adata: ad.AnnData,
    config: AnalysisConfig,
    condition_counts: Mapping[str, int],
    warnings: list[str],
    *,
    reason: str,
    donors_per_condition: Mapping[str, int] | None = None,
) -> InputAudit:
    return InputAudit(
        branch=AnalysisBranch.EXPLORATORY_NO_DONOR,
        reasons=(reason, "Per-cell tests are exploratory and cannot verify a headline claim."),
        warnings=tuple(warnings),
        n_cells=int(adata.n_obs),
        n_genes=int(adata.n_vars),
        condition_counts=dict(condition_counts),
        donors_per_condition=dict(donors_per_condition or {}),
        counts_layer=config.counts_layer,
        raw_counts_valid=True,
    )


def _clean_labels(series: pd.Series) -> pd.Series:
    """String-normalise labels while preserving missing values as missing."""

    result = series.astype("object").copy()
    missing = pd.isna(result)
    result.loc[~missing] = result.loc[~missing].map(lambda value: str(value).strip())
    result.loc[result == ""] = np.nan
    return result


__all__ = [
    "AnalysisBranch",
    "DataValidationError",
    "InputAudit",
    "audit_input",
    "decide_analysis_branch",
    "extract_raw_counts",
    "get_raw_counts",
    "load_adata",
    "load_h5ad",
    "missing_required_genes",
    "required_genes",
    "retrieve_raw_counts",
    "validate_genes",
    "validate_input",
    "validate_metadata",
    "validate_raw_counts",
]
