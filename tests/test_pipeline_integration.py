from __future__ import annotations

import json

import pytest

from tcell_exhaustion.demo import demo_config, write_demo_h5ad
from tcell_exhaustion.pipeline import run_pipeline


@pytest.mark.integration
def test_complete_demo_recovers_registered_truth(tmp_path) -> None:
    data_path = tmp_path / "demo.h5ad"
    output_dir = tmp_path / "run"
    write_demo_h5ad(data_path, seed=42, cells_per_subtype_per_donor=8)

    result = run_pipeline(demo_config(data_path, output_dir, seed=42))

    assert result.branch == "donor_aware"
    assert result.headline_subtype == "terminally_exhausted"
    assert result.headline_significant
    assert result.robust
    required = [
        output_dir / "figures" / "02_annotated_cd8_umap.png",
        output_dir / "figures" / "03_exhaustion_violin.png",
        output_dir / "figures" / "04_pseudobulk_volcano.png",
        output_dir / "figures" / "05_resolution_robustness.png",
        output_dir / "tables" / "reviewer_findings.csv",
        output_dir / "report.md",
        output_dir / "provenance" / "manifest.json",
    ]
    assert all(path.is_file() and path.stat().st_size > 0 for path in required)
    manifest = json.loads((output_dir / "provenance" / "manifest.json").read_text())
    assert manifest["result_summary"]["headline"]["subtype"] == "terminally_exhausted"

