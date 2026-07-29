from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from tcell_exhaustion.config import AnalysisConfig, ConfigError
from tcell_exhaustion.data import (
    AnalysisBranch,
    DataValidationError,
    audit_input,
    validate_raw_counts,
)
from tcell_exhaustion.demo import generate_demo_adata


def test_config_loads_nested_yaml_and_project_defaults(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
input_path: data/cells.h5ad
output_dir: results
obs_keys:
  condition: treatment
  donor: participant
conditions:
  a: control
  b: chronic
""".strip(),
        encoding="utf-8",
    )

    config = AnalysisConfig.from_yaml(config_path)

    assert config.input_path == (tmp_path / "data/cells.h5ad").resolve()
    assert config.output_dir == (tmp_path / "results").resolve()
    assert (config.condition_key, config.donor_key) == ("treatment", "participant")
    assert (config.condition_a, config.condition_b) == ("control", "chronic")
    assert config.counts_layer == "counts"
    assert config.resolutions == (0.4, 0.6, 0.8, 1.0)
    assert config.effector_memory_rule.positive == ("GZMK", "NKG7", "IL7R")
    assert config.exhaustion_genes == ("PDCD1", "HAVCR2", "LAG3", "TOX", "TIGIT", "ENTPD1")


def test_config_rejects_missing_paths_and_unknown_knobs():
    with pytest.raises(ConfigError, match="Missing required"):
        AnalysisConfig.from_mapping({"output_dir": "out"})
    with pytest.raises(ConfigError, match="Unknown config"):
        AnalysisConfig.from_mapping(
            {"input_path": "cells.h5ad", "output_dir": "out", "post_hoc_markers": ["X"]}
        )


@pytest.mark.parametrize(
    "counts, message",
    [
        (np.array([[1.0, 0.5]]), "non-integer"),
        (sparse.csr_matrix([[1, -1]]), "negative"),
        (np.array([[1.0, np.nan]]), "NaN"),
    ],
)
def test_raw_count_validation_rejects_invalid_values(counts, message):
    with pytest.raises(DataValidationError, match=message):
        validate_raw_counts(counts)


def test_audit_selects_predeclared_branches(tmp_path):
    adata = generate_demo_adata(cells_per_subtype_per_donor=3, cd4_cells_per_donor=1)
    config = AnalysisConfig(input_path=tmp_path / "demo.h5ad", output_dir=tmp_path / "out")

    donor_audit = audit_input(adata, config)
    assert donor_audit.branch == AnalysisBranch.DONOR_AWARE
    assert donor_audit.donors_per_condition == {"A": 6, "B": 6}

    no_donor = adata.copy()
    del no_donor.obs["donor"]
    assert audit_input(no_donor, config).branch == AnalysisBranch.EXPLORATORY_NO_DONOR

    one_condition = adata[adata.obs["condition"] == "A"].copy()
    assert audit_input(one_condition, config).branch == AnalysisBranch.MARKER_FALLBACK

    invalid = adata.copy()
    invalid.layers["counts"] = invalid.layers["counts"].astype(float)
    invalid.layers["counts"][0, 0] = 0.25
    blocked = audit_input(invalid, config)
    assert blocked.branch == AnalysisBranch.BLOCKED
    assert not blocked.raw_counts_valid
