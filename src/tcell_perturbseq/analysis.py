"""Transparent candidate prioritization on the official supplementary tables."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tcell_perturbseq.config import AnalysisConfig
from tcell_perturbseq.sources import coerce_boolean

PERCENTILE_COLUMNS = (
    "n_downstream_percentile",
    "crossdonor_min_percentile",
    "crossguide_percentile",
)


@dataclass(frozen=True)
class AnalysisResults:
    """All in-memory tables emitted by one lightweight analysis run."""

    source_qc_decisions: pd.DataFrame
    filter_funnel: pd.DataFrame
    candidate_scores: pd.DataFrame
    top_candidates_by_condition: pd.DataFrame
    cross_condition_candidates: pd.DataFrame
    validation_donor_deltas: pd.DataFrame
    validation_summary: pd.DataFrame
    sample_design_summary: pd.DataFrame
    candidate_polarization_coefficients: pd.DataFrame

    def tables(self) -> dict[str, pd.DataFrame]:
        """Map stable artifact stems to result frames."""

        return {
            "source_qc_decisions": self.source_qc_decisions,
            "filter_funnel": self.filter_funnel,
            "candidate_scores": self.candidate_scores,
            "top_candidates_by_condition": self.top_candidates_by_condition,
            "cross_condition_candidates": self.cross_condition_candidates,
            "validation_donor_deltas": self.validation_donor_deltas,
            "validation_summary": self.validation_summary,
            "sample_design_summary": self.sample_design_summary,
            "candidate_polarization_coefficients": (self.candidate_polarization_coefficients),
        }


def _append_failure_reason(
    reasons: np.ndarray,
    failed: pd.Series,
    label: str,
) -> np.ndarray:
    failed_values = failed.to_numpy(dtype=bool)
    existing = reasons != ""
    reasons = np.where(
        failed_values & existing,
        reasons + ";" + label,
        np.where(failed_values, label, reasons),
    )
    return reasons


def build_source_qc_decisions(
    de_stats: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """Apply the six declared hard gates and retain every decision for auditing."""

    frame = de_stats.copy().rename(
        columns={
            "target_contrast_gene_name": "gene",
            "crossdonor_correlation_min": "crossdonor_min",
            "crossguide_correlation": "crossguide",
        }
    )
    numeric_columns = (
        "n_cells_target",
        "n_downstream",
        "ontarget_effect_size",
        "crossdonor_min",
        "crossguide",
    )
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["ontarget_significant"] = coerce_boolean(
        frame["ontarget_significant"], column="ontarget_significant"
    ).fillna(False)
    frame["offtarget_flag"] = coerce_boolean(
        frame["offtarget_flag"], column="offtarget_flag"
    ).fillna(True)

    frame["gate_ontarget_significant"] = frame["ontarget_significant"].astype(bool)
    frame["gate_negative_ontarget_effect"] = frame["ontarget_effect_size"].lt(0)
    frame["gate_no_offtarget_flag"] = ~frame["offtarget_flag"].astype(bool)
    frame["gate_min_cells"] = frame["n_cells_target"].ge(config.min_cells_target)
    frame["gate_crossdonor_present"] = frame["crossdonor_min"].notna()
    frame["gate_crossdonor_positive"] = frame["crossdonor_min"].gt(0)
    frame["gate_crossguide_present"] = frame["crossguide"].notna()
    frame["gate_crossguide_positive"] = frame["crossguide"].gt(0)
    gate_columns = [column for column in frame.columns if column.startswith("gate_")]
    frame["source_qc_pass"] = frame[gate_columns].all(axis=1)

    reasons = np.full(len(frame), "", dtype=object)
    labels = (
        ("gate_ontarget_significant", "on_target_not_significant"),
        ("gate_negative_ontarget_effect", "on_target_effect_not_negative"),
        ("gate_no_offtarget_flag", "off_target_flagged"),
        ("gate_min_cells", f"fewer_than_{config.min_cells_target}_target_cells"),
        ("gate_crossdonor_present", "cross_donor_metric_missing"),
        ("gate_crossdonor_positive", "cross_donor_metric_not_positive"),
        ("gate_crossguide_present", "cross_guide_metric_missing"),
        ("gate_crossguide_positive", "cross_guide_metric_not_positive"),
    )
    for column, label in labels:
        reasons = _append_failure_reason(reasons, ~frame[column], label)
    frame["qc_failure_reasons"] = reasons

    preferred = [
        "gene",
        "culture_condition",
        "target_contrast",
        "n_cells_target",
        "n_downstream",
        "ontarget_effect_size",
        "ontarget_significant",
        "offtarget_flag",
        "crossdonor_min",
        "crossguide",
        *gate_columns,
        "source_qc_pass",
        "qc_failure_reasons",
    ]
    remaining = [column for column in frame.columns if column not in preferred]
    return (
        frame[preferred + remaining]
        .sort_values(["culture_condition", "gene"], kind="stable")
        .reset_index(drop=True)
    )


def build_filter_funnel(
    decisions: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """Count rows after each sequential hard gate, separately by condition."""

    stages = (
        ("all_screen_rows", None),
        ("on_target_significant", "gate_ontarget_significant"),
        ("negative_on_target_effect", "gate_negative_ontarget_effect"),
        ("off_target_flag_false", "gate_no_offtarget_flag"),
        (f"n_cells_target_at_least_{config.min_cells_target}", "gate_min_cells"),
        (
            "cross_donor_metric_present_and_positive",
            ("gate_crossdonor_present", "gate_crossdonor_positive"),
        ),
        (
            "cross_guide_metric_present_and_positive",
            ("gate_crossguide_present", "gate_crossguide_positive"),
        ),
    )
    rows: list[dict[str, object]] = []
    for condition in config.conditions:
        condition_frame = decisions[decisions["culture_condition"].eq(condition)]
        cumulative = pd.Series(True, index=condition_frame.index, dtype=bool)
        for order, (stage, columns) in enumerate(stages):
            if isinstance(columns, str):
                cumulative &= condition_frame[columns].astype(bool)
            elif columns is not None:
                for column in columns:
                    cumulative &= condition_frame[column].astype(bool)
            rows.append(
                {
                    "culture_condition": condition,
                    "stage_order": order,
                    "stage": stage,
                    "n_rows": int(cumulative.sum()),
                }
            )
    return pd.DataFrame(rows)


def score_candidates(
    decisions: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """Rank three source metrics within condition and combine them geometrically.

    ``n_downstream`` is the authors' 10% FDR discovery count, not an effect size. The source
    correlations are author-reported values; this lightweight workflow does not recompute them.
    """

    candidates = decisions.loc[decisions["source_qc_pass"]].copy()
    metrics = {
        "n_downstream": "n_downstream_percentile",
        "crossdonor_min": "crossdonor_min_percentile",
        "crossguide": "crossguide_percentile",
    }
    for metric, percentile in metrics.items():
        candidates[percentile] = candidates.groupby("culture_condition", sort=False)[metric].rank(
            method="average", pct=True
        )
    candidates["priority_score"] = np.cbrt(
        candidates["n_downstream_percentile"]
        * candidates["crossdonor_min_percentile"]
        * candidates["crossguide_percentile"]
    )
    candidates["rank_within_condition"] = (
        candidates.groupby("culture_condition", sort=False)["priority_score"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    candidates["candidate_label"] = "source-QC pass"
    condition_order = {condition: index for index, condition in enumerate(config.conditions)}
    candidates["_condition_order"] = candidates["culture_condition"].map(condition_order)
    return (
        candidates.sort_values(
            ["_condition_order", "priority_score", "gene"],
            ascending=[True, False, True],
            kind="stable",
        )
        .drop(columns="_condition_order")
        .reset_index(drop=True)
    )


def select_top_candidates(
    candidates: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """Return the configured number of highest composite scores per condition."""

    return (
        candidates.sort_values(
            ["culture_condition", "rank_within_condition", "gene"], kind="stable"
        )
        .groupby("culture_condition", sort=False, group_keys=False)
        .head(config.top_n)
        .reset_index(drop=True)
    )


def build_cross_condition_candidates(
    candidates: pd.DataFrame,
    config: AnalysisConfig,
) -> pd.DataFrame:
    """Rank genes passing every condition by their weakest condition-specific score."""

    score_columns = [f"{condition}_priority_score" for condition in config.conditions]
    output_columns = [
        "gene",
        *score_columns,
        "min_priority_score",
        "mean_priority_score",
        "worst_condition",
        "cross_condition_rank",
        "candidate_label",
    ]
    if candidates.empty:
        return pd.DataFrame(columns=output_columns)
    pivot = candidates.pivot(
        index="gene", columns="culture_condition", values="priority_score"
    ).reindex(columns=config.conditions)
    complete = pivot.dropna(subset=list(config.conditions)).copy()
    if complete.empty:
        return pd.DataFrame(columns=output_columns)
    complete.columns = score_columns
    complete["min_priority_score"] = complete[score_columns].min(axis=1)
    complete["mean_priority_score"] = complete[score_columns].mean(axis=1)
    weakest_indices = complete[score_columns].to_numpy().argmin(axis=1)
    complete["worst_condition"] = [config.conditions[index] for index in weakest_indices]
    complete["cross_condition_rank"] = (
        complete["min_priority_score"].rank(method="min", ascending=False).astype(int)
    )
    complete["candidate_label"] = "reproducible candidate"
    return (
        complete.reset_index()
        .sort_values(
            ["cross_condition_rank", "mean_priority_score", "gene"],
            ascending=[True, False, True],
            kind="stable",
        )[output_columns]
        .reset_index(drop=True)
    )


def calculate_validation_deltas(
    validation: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Subtract each donor's mean NTC measurement and summarize without p-values."""

    frame = validation.copy().rename(
        columns={"Sample": "sample", "Donor": "donor", "Perturbation": "perturbation"}
    )
    for column in ("IL10_perc", "IL21_perc"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    control_mask = (
        frame["perturbation"].astype(str).str.fullmatch(r"NTC[123]?", case=False, na=False)
    )
    controls = (
        frame.loc[control_mask]
        .groupby("donor", observed=True)
        .agg(
            control_n=("sample", "size"),
            IL10_control_mean=("IL10_perc", "mean"),
            IL21_control_mean=("IL21_perc", "mean"),
        )
        .reset_index()
    )
    deltas = frame.loc[~control_mask].merge(
        controls, on="donor", how="left", validate="many_to_one"
    )
    deltas["IL10_delta_vs_donor_NTC"] = deltas["IL10_perc"] - deltas["IL10_control_mean"]
    deltas["IL21_delta_vs_donor_NTC"] = deltas["IL21_perc"] - deltas["IL21_control_mean"]
    delta_columns = [
        "sample",
        "donor",
        "perturbation",
        "control_n",
        "IL10_perc",
        "IL10_control_mean",
        "IL10_delta_vs_donor_NTC",
        "IL21_perc",
        "IL21_control_mean",
        "IL21_delta_vs_donor_NTC",
    ]
    deltas = (
        deltas[delta_columns]
        .sort_values(["perturbation", "donor", "sample"], kind="stable")
        .reset_index(drop=True)
    )
    summary = (
        deltas.groupby("perturbation", observed=True)
        .agg(
            n_donors=("donor", "nunique"),
            IL10_mean_delta=("IL10_delta_vs_donor_NTC", "mean"),
            IL10_median_delta=("IL10_delta_vs_donor_NTC", "median"),
            IL10_min_delta=("IL10_delta_vs_donor_NTC", "min"),
            IL10_max_delta=("IL10_delta_vs_donor_NTC", "max"),
            IL21_mean_delta=("IL21_delta_vs_donor_NTC", "mean"),
            IL21_median_delta=("IL21_delta_vs_donor_NTC", "median"),
            IL21_min_delta=("IL21_delta_vs_donor_NTC", "min"),
            IL21_max_delta=("IL21_delta_vs_donor_NTC", "max"),
        )
        .reset_index()
        .sort_values(["IL10_mean_delta", "perturbation"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return deltas, summary


def summarize_sample_design(metadata: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Summarize the official repeated-donor screen design without demographic fields."""

    summary = (
        metadata.groupby("culture_condition", observed=True)
        .agg(
            n_samples=("cell_sample_id", "nunique"),
            n_donors=("donor_id", "nunique"),
            n_runs=("10xrun_id", "nunique"),
            n_libraries=("library_id", "nunique"),
        )
        .reindex(config.conditions)
        .reset_index()
    )
    return summary


def select_candidate_coefficients(
    coefficients: pd.DataFrame,
    candidates: pd.DataFrame,
    top_candidates: pd.DataFrame,
    cross_condition: pd.DataFrame,
) -> pd.DataFrame:
    """Retain official polarization-model annotations for prioritized genes."""

    candidate_genes = set(candidates["gene"].astype(str))
    top_genes = set(top_candidates["gene"].astype(str))
    cross_genes = set(cross_condition["gene"].astype(str))
    selected = coefficients.loc[coefficients["regulator"].astype(str).isin(candidate_genes)].copy()
    selected["in_top_candidates_by_condition"] = selected["regulator"].astype(str).isin(top_genes)
    selected["in_cross_condition_candidates"] = selected["regulator"].astype(str).isin(cross_genes)
    return selected.sort_values(
        ["in_cross_condition_candidates", "in_top_candidates_by_condition", "coef_rank"],
        ascending=[False, False, False],
        kind="stable",
    ).reset_index(drop=True)


def analyze_tables(
    tables: dict[str, pd.DataFrame],
    config: AnalysisConfig,
) -> AnalysisResults:
    """Run all deterministic table transformations after source auditing."""

    decisions = build_source_qc_decisions(tables["de_stats"], config)
    funnel = build_filter_funnel(decisions, config)
    candidates = score_candidates(decisions, config)
    top = select_top_candidates(candidates, config)
    cross = build_cross_condition_candidates(candidates, config)
    deltas, validation_summary = calculate_validation_deltas(tables["arrayed_validation"])
    design = summarize_sample_design(tables["sample_metadata"], config)
    coefficients = select_candidate_coefficients(
        tables["polarization_coefficients"], candidates, top, cross
    )
    return AnalysisResults(
        source_qc_decisions=decisions,
        filter_funnel=funnel,
        candidate_scores=candidates,
        top_candidates_by_condition=top,
        cross_condition_candidates=cross,
        validation_donor_deltas=deltas,
        validation_summary=validation_summary,
        sample_design_summary=design,
        candidate_polarization_coefficients=coefficients,
    )
