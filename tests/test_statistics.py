"""Deterministic tests for the transparent statistical core."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from tcell_exhaustion.statistics import (
    benjamini_hochberg,
    build_reviewer_table,
    donor_module_statistics,
    per_cell_de,
    pseudobulk_de,
)


def test_benjamini_hochberg_preserves_order_shape_and_missing_values() -> None:
    pvalues = np.array([[0.01, 0.04, np.nan], [0.03, 0.002, 1.0]])

    adjusted = benjamini_hochberg(pvalues)

    expected = np.array([[0.025, 0.05, np.nan], [0.05, 0.01, 1.0]])
    np.testing.assert_allclose(adjusted, expected, equal_nan=True)
    assert adjusted.shape == pvalues.shape


@pytest.mark.parametrize("bad_value", [-0.01, 1.01, np.inf])
def test_benjamini_hochberg_rejects_invalid_pvalues(bad_value: float) -> None:
    with pytest.raises(ValueError):
        benjamini_hochberg([0.05, bad_value])


def test_donor_module_statistics_uses_equal_donor_weight() -> None:
    # Donor A1 contributes many low-scoring cells.  Correct donor aggregation
    # makes its mean one unit rather than giving those cells extra weight.
    obs = pd.DataFrame(
        {
            "subtype": ["terminal"] * 10 + ["memory"] * 2,
            "condition": ["A"] * 6 + ["B"] * 4 + ["A", "B"],
            "donor": ["A1"] * 5 + ["A2", "B1", "B1", "B2", "B2", "A1", "B1"],
            "exhaustion_score": [0, 0, 0, 0, 0, 2, 4, 4, 6, 6, 1, 1],
        }
    )

    result = donor_module_statistics(
        obs,
        subtype_key="subtype",
        condition_key="condition",
        condition_a="A",
        condition_b="B",
        donor_key="donor",
    ).set_index("subtype")

    terminal = result.loc["terminal"]
    assert terminal["mean_a"] == pytest.approx(1.0)
    assert terminal["mean_b"] == pytest.approx(5.0)
    assert terminal["delta"] == pytest.approx(4.0)
    assert terminal["n_donors_a"] == 2
    assert terminal["n_donors_b"] == 2
    assert terminal["t_statistic"] > 0
    assert bool(terminal["donor_aware"])
    assert result.loc["memory", "test_status"] == "NOT_TESTABLE"
    assert np.isnan(result.loc["memory", "p_adj"])


def test_donor_module_statistics_labels_no_donor_fallback_exploratory() -> None:
    obs = pd.DataFrame(
        {
            "subtype": ["terminal"] * 6,
            "condition": ["A"] * 3 + ["B"] * 3,
            "exhaustion_score": [0.0, 0.1, 0.2, 1.0, 1.1, 1.2],
        }
    )

    row = donor_module_statistics(obs, "subtype", "condition", "A", "B", donor_key=None).iloc[0]

    assert not bool(row["donor_aware"])
    assert row["n_units_a"] == 3
    assert "exploratory" in row["analysis_unit"]


def test_pseudobulk_de_sums_sparse_counts_and_tests_donors() -> None:
    obs = pd.DataFrame(
        {
            "subtype": ["terminal"] * 12,
            "condition": ["A"] * 6 + ["B"] * 6,
            "donor": ["A1", "A1", "A2", "A2", "A3", "A3", "B1", "B1", "B2", "B2", "B3", "B3"],
        }
    )
    # Each donor totals 200 reads after its two cells are summed.  This keeps
    # the CPM denominator fixed while UP and DOWN exchange abundance.
    per_cell_counts = np.array(
        [[5, 45, 50], [5, 45, 50]] * 3 + [[45, 5, 50], [45, 5, 50]] * 3,
        dtype=float,
    )

    result = pseudobulk_de(
        sparse.csr_matrix(per_cell_counts),
        obs,
        ["UP", "DOWN", "STABLE"],
        "subtype",
        "terminal",
        "condition",
        "A",
        "B",
        "donor",
    ).set_index("gene")

    assert result.loc["UP", "log2fc"] > 0
    assert result.loc["DOWN", "log2fc"] < 0
    assert result.loc["STABLE", "log2fc"] == pytest.approx(0.0)
    assert result.loc["UP", "p_adj"] == pytest.approx(0.0)
    assert result.loc["STABLE", "p_adj"] == pytest.approx(1.0)
    assert result.loc["UP", "n_donors_a"] == 3
    assert result.loc["UP", "n_donors_b"] == 3


def test_pseudobulk_de_returns_not_testable_when_a_condition_is_missing() -> None:
    obs = pd.DataFrame({"subtype": ["terminal"], "condition": ["A"], "donor": ["A1"]})

    result = pseudobulk_de(
        sparse.csr_matrix([[1, 2]]),
        obs,
        ["G1", "G2"],
        "subtype",
        "terminal",
        "condition",
        "A",
        "B",
        "donor",
    )

    assert result["test_status"].eq("NOT_TESTABLE").all()
    assert result["p_adj"].isna().all()


def test_per_cell_de_is_mann_whitney_and_explicitly_exploratory() -> None:
    obs = pd.DataFrame(
        {
            "subtype": ["terminal"] * 8,
            "condition": ["A"] * 4 + ["B"] * 4,
        }
    )
    expression = sparse.csr_matrix(
        np.array(
            [
                [0.0, 2.0],
                [0.1, 2.0],
                [0.2, 2.0],
                [0.3, 2.0],
                [3.0, 2.0],
                [3.1, 2.0],
                [3.2, 2.0],
                [3.3, 2.0],
            ]
        )
    )

    result = per_cell_de(
        expression,
        obs,
        ["UP", "TIED"],
        "subtype",
        "terminal",
        "condition",
        "A",
        "B",
    ).set_index("gene")

    assert result.loc["UP", "log2fc"] > 0
    assert result.loc["UP", "rank_biserial"] == pytest.approx(1.0)
    assert result.loc["TIED", "p_value"] == pytest.approx(1.0)
    assert bool(result.loc["UP", "exploratory"])
    assert "not an independent" in result.loc["UP", "analysis_unit"]


def test_reviewer_table_assigns_all_donor_statuses_and_requires_evidence() -> None:
    per_cell = pd.DataFrame(
        {
            "gene": ["VERIFIED_GENE", "PENDING_GENE", "WEAK_GENE", "REVERSED_GENE", "MISSING_GENE"],
            "log2fc": [2.0, 1.5, 1.0, 1.0, -1.0],
            "p_value": [1e-10, 2e-9, 3e-8, 4e-7, 5e-6],
            "p_adj": [5e-10, 5e-9, 5e-8, 5e-7, 5e-6],
        }
    )
    pseudobulk = pd.DataFrame(
        {
            "gene": ["VERIFIED_GENE", "PENDING_GENE", "WEAK_GENE", "REVERSED_GENE"],
            "log2fc": [1.0, 0.8, 0.5, -0.5],
            "p_value": [0.001, 0.002, 0.1, 0.001],
            "p_adj": [0.004, 0.008, 0.2, 0.004],
        }
    )
    evidence = pd.DataFrame(
        {
            "gene": ["VERIFIED_GENE", "PENDING_GENE", "WEAK_GENE", "REVERSED_GENE"],
            "evidence_pass": [True, False, True, True],
            "citation": ["PMID:1", "PMID:2", "PMID:3", "PMID:4"],
        }
    )

    result = build_reviewer_table(per_cell, pseudobulk, evidence, top_n=5).set_index("gene")

    assert result.loc["VERIFIED_GENE", "status"] == "SURVIVES"
    assert result.loc["VERIFIED_GENE", "final_status"] == "VERIFIED"
    assert result.loc["PENDING_GENE", "status"] == "SURVIVES"
    assert result.loc["PENDING_GENE", "final_status"] == "NOT_VERIFIED"
    assert result.loc["WEAK_GENE", "status"] == "DOES_NOT_SURVIVE"
    assert result.loc["REVERSED_GENE", "status"] == "DIRECTION_REVERSES"
    assert result.loc["MISSING_GENE", "status"] == "NOT_TESTABLE"
    assert result.loc["VERIFIED_GENE", "evidence_citation"] == "PMID:1"
    assert result.loc["VERIFIED_GENE", "pseudoreplication_delta_log10"] > 0


def test_reviewer_table_never_verifies_without_explicit_pass() -> None:
    per_cell = pd.DataFrame({"gene": ["G"], "log2fc": [1.0], "p_value": [1e-6], "p_adj": [1e-6]})
    pseudobulk = pd.DataFrame({"gene": ["G"], "log2fc": [0.5], "p_value": [0.01], "p_adj": [0.02]})

    no_evidence = build_reviewer_table(per_cell, pseudobulk)
    citation_only = build_reviewer_table(
        per_cell, pseudobulk, pd.DataFrame({"gene": ["G"], "citation": ["PMID:1"]})
    )

    assert no_evidence.loc[0, "status"] == "SURVIVES"
    assert no_evidence.loc[0, "final_status"] == "NOT_VERIFIED"
    assert citation_only.loc[0, "final_status"] == "NOT_VERIFIED"


def test_count_matrix_validation_rejects_negative_raw_counts() -> None:
    obs = pd.DataFrame({"subtype": ["terminal"], "condition": ["A"], "donor": ["A1"]})

    with pytest.raises(ValueError, match="non-negative"):
        pseudobulk_de(
            np.array([[-1.0]]),
            obs,
            ["G"],
            "subtype",
            "terminal",
            "condition",
            "A",
            "B",
            "donor",
        )
