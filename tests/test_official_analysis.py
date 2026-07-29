from __future__ import annotations

import pandas as pd
import pytest

from tcell_perturbseq.analysis import (
    analyze_tables,
    build_cross_condition_candidates,
    build_filter_funnel,
    build_source_qc_decisions,
    calculate_validation_deltas,
    score_candidates,
)
from tcell_perturbseq.config import OFFICIAL_CONDITIONS, AnalysisConfig


def make_de_frame(*, include_failures: bool = True) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for condition in OFFICIAL_CONDITIONS:
        for index, gene in enumerate(("GENE_A", "GENE_B", "GENE_C"), start=1):
            rows.append(
                {
                    "target_contrast_gene_name": gene,
                    "culture_condition": condition,
                    "target_contrast": f"ENSG_{gene}",
                    "n_cells_target": 100 + index,
                    "n_up_genes": index,
                    "n_down_genes": index,
                    "n_total_de_genes": index * 2,
                    "ontarget_effect_size": -float(index),
                    "ontarget_significant": True,
                    "offtarget_flag": False,
                    "n_downstream": index * 10,
                    "crossdonor_correlation_min": index / 10,
                    "crossguide_correlation": index / 10,
                }
            )
    if include_failures:
        base = rows[0].copy()
        failures = (
            ("FAIL_SIGNIFICANCE", {"ontarget_significant": False}),
            ("FAIL_DIRECTION", {"ontarget_effect_size": 0.2}),
            ("FAIL_OFFTARGET", {"offtarget_flag": True}),
            ("FAIL_CELLS", {"n_cells_target": 99}),
            ("FAIL_DONOR_MISSING", {"crossdonor_correlation_min": None}),
            ("FAIL_DONOR_SIGN", {"crossdonor_correlation_min": 0.0}),
            ("FAIL_GUIDE_MISSING", {"crossguide_correlation": None}),
            ("FAIL_GUIDE_SIGN", {"crossguide_correlation": -0.1}),
        )
        for gene, changes in failures:
            row = base | {"target_contrast_gene_name": gene, "target_contrast": f"ENSG_{gene}"}
            row.update(changes)
            rows.append(row)
    return pd.DataFrame(rows)


def make_validation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Sample": "d1_ntc1",
                "IL10_perc": 1.0,
                "IL21_perc": 2.0,
                "Donor": "D1",
                "Perturbation": "NTC1",
            },
            {
                "Sample": "d1_ntc2",
                "IL10_perc": 3.0,
                "IL21_perc": 4.0,
                "Donor": "D1",
                "Perturbation": "NTC2",
            },
            {
                "Sample": "d1_a",
                "IL10_perc": 5.0,
                "IL21_perc": 1.0,
                "Donor": "D1",
                "Perturbation": "GENE_A",
            },
            {
                "Sample": "d2_ntc",
                "IL10_perc": 2.0,
                "IL21_perc": 2.0,
                "Donor": "D2",
                "Perturbation": "NTC",
            },
            {
                "Sample": "d2_a",
                "IL10_perc": 3.0,
                "IL21_perc": 6.0,
                "Donor": "D2",
                "Perturbation": "GENE_A",
            },
        ]
    )


def test_hard_gates_are_all_required() -> None:
    config = AnalysisConfig()
    decisions = build_source_qc_decisions(make_de_frame(), config)

    passing = decisions.loc[decisions["source_qc_pass"], "gene"]
    assert set(passing) == {"GENE_A", "GENE_B", "GENE_C"}
    assert len(passing) == 9
    failures = decisions.loc[~decisions["source_qc_pass"]].set_index("gene")
    assert "on_target_not_significant" in failures.loc["FAIL_SIGNIFICANCE", "qc_failure_reasons"]
    assert "on_target_effect_not_negative" in failures.loc["FAIL_DIRECTION", "qc_failure_reasons"]
    assert "off_target_flagged" in failures.loc["FAIL_OFFTARGET", "qc_failure_reasons"]
    assert "fewer_than_100_target_cells" in failures.loc["FAIL_CELLS", "qc_failure_reasons"]
    assert "cross_donor_metric_missing" in failures.loc["FAIL_DONOR_MISSING", "qc_failure_reasons"]
    assert (
        "cross_guide_metric_not_positive" in failures.loc["FAIL_GUIDE_SIGN", "qc_failure_reasons"]
    )


def test_percentiles_geometric_score_and_cross_condition_minimum() -> None:
    config = AnalysisConfig(top_n=1)
    decisions = build_source_qc_decisions(make_de_frame(include_failures=False), config)
    scores = score_candidates(decisions, config)

    rest = scores[scores["culture_condition"].eq("Rest")].set_index("gene")
    assert rest.loc["GENE_A", "n_downstream_percentile"] == pytest.approx(1 / 3)
    assert rest.loc["GENE_B", "crossdonor_min_percentile"] == pytest.approx(2 / 3)
    assert rest.loc["GENE_C", "priority_score"] == pytest.approx(1.0)
    assert rest.loc["GENE_A", "priority_score"] == pytest.approx(1 / 3)

    cross = build_cross_condition_candidates(scores, config)
    assert list(cross["gene"]) == ["GENE_C", "GENE_B", "GENE_A"]
    assert cross.iloc[0]["min_priority_score"] == pytest.approx(1.0)
    assert cross.iloc[0]["candidate_label"] == "reproducible candidate"


def test_filter_funnel_is_sequential_and_condition_specific() -> None:
    config = AnalysisConfig()
    decisions = build_source_qc_decisions(make_de_frame(), config)
    funnel = build_filter_funnel(decisions, config)

    rest = funnel[funnel["culture_condition"].eq("Rest")].sort_values("stage_order")
    assert rest.iloc[0]["n_rows"] == 11
    assert rest.iloc[-1]["n_rows"] == 3
    assert rest["n_rows"].is_monotonic_decreasing
    for condition in ("Stim8hr", "Stim48hr"):
        subset = funnel[funnel["culture_condition"].eq(condition)].sort_values("stage_order")
        assert subset.iloc[0]["n_rows"] == 3
        assert subset.iloc[-1]["n_rows"] == 3


def test_validation_uses_mean_ntc_within_donor_and_no_p_values() -> None:
    deltas, summary = calculate_validation_deltas(make_validation_frame())

    d1 = deltas[deltas["donor"].eq("D1")].iloc[0]
    assert d1["control_n"] == 2
    assert d1["IL10_control_mean"] == pytest.approx(2.0)
    assert d1["IL10_delta_vs_donor_NTC"] == pytest.approx(3.0)
    assert d1["IL21_delta_vs_donor_NTC"] == pytest.approx(-2.0)
    gene_a = summary.set_index("perturbation").loc["GENE_A"]
    assert gene_a["n_donors"] == 2
    assert gene_a["IL10_mean_delta"] == pytest.approx(2.0)
    assert gene_a["IL21_mean_delta"] == pytest.approx(1.0)
    assert not any("p_value" in column or "p_adj" in column for column in summary.columns)


def test_full_analysis_joins_only_candidate_polarization_rows() -> None:
    config = AnalysisConfig(top_n=1)
    metadata = pd.DataFrame(
        [
            {
                "cell_sample_id": f"{condition}_D1",
                "10xrun_id": "R1",
                "donor_id": "D1",
                "culture_condition": condition,
                "library_id": f"lib_{condition}",
            }
            for condition in OFFICIAL_CONDITIONS
        ]
    )
    coefficients = pd.DataFrame(
        [
            {
                "coef_mean": 0.5,
                "coef_sem": 0.1,
                "coef_rank": 0.9,
                "regulator": gene,
                "dataset_key": "polarization_Rest",
                "signature": "polarization",
            }
            for gene in ("GENE_A", "NOT_A_CANDIDATE")
        ]
    )
    tables = {
        "de_stats": make_de_frame(include_failures=False),
        "sample_metadata": metadata,
        "arrayed_validation": make_validation_frame(),
        "polarization_coefficients": coefficients,
    }
    results = analyze_tables(tables, config)

    assert set(results.candidate_polarization_coefficients["regulator"]) == {"GENE_A"}
    assert len(results.top_candidates_by_condition) == 3
