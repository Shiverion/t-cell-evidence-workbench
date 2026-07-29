from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import pytest

from tcell_perturbseq.analysis import analyze_tables
from tcell_perturbseq.cli import build_parser
from tcell_perturbseq.config import OFFICIAL_CONDITIONS, AnalysisConfig
from tcell_perturbseq.plotting import write_figures
from tcell_perturbseq.reporting import (
    write_manifest,
    write_methods,
    write_report,
    write_result_tables,
    write_source_audit,
)
from tcell_perturbseq.sources import (
    PINNED_COMMIT,
    SOURCE_SPECS,
    SourceSchemaError,
    SourceSpec,
    audit_source_tables,
    download_sources,
)


def tiny_tables() -> dict[str, pd.DataFrame]:
    de_rows = []
    for condition in OFFICIAL_CONDITIONS:
        for index, gene in enumerate(("A", "B"), start=1):
            de_rows.append(
                {
                    "target_contrast_gene_name": gene,
                    "culture_condition": condition,
                    "target_contrast": f"ENSG{index}",
                    "n_cells_target": 150,
                    "ontarget_effect_size": -index,
                    "ontarget_significant": True,
                    "offtarget_flag": False,
                    "n_downstream": index * 10,
                    "crossdonor_correlation_min": index / 10,
                    "crossguide_correlation": index / 10,
                }
            )
    metadata = pd.DataFrame(
        [
            {
                "cell_sample_id": f"{condition}_D1",
                "10xrun_id": "R1",
                "donor_id": "D1",
                "culture_condition": condition,
                "library_id": f"library_{condition}",
            }
            for condition in OFFICIAL_CONDITIONS
        ]
    )
    validation = pd.DataFrame(
        [
            {
                "Sample": "D1_NTC",
                "IL10_perc": 1.0,
                "IL21_perc": 2.0,
                "Donor": "D1",
                "Perturbation": "NTC",
            },
            {
                "Sample": "D1_A",
                "IL10_perc": 3.0,
                "IL21_perc": 4.0,
                "Donor": "D1",
                "Perturbation": "A",
            },
        ]
    )
    coefficients = pd.DataFrame(
        [
            {
                "coef_mean": 0.4,
                "coef_sem": 0.1,
                "coef_rank": 0.8,
                "regulator": "A",
                "dataset_key": "polarization_Rest",
                "signature": "polarization",
            }
        ]
    )
    return {
        "de_stats": pd.DataFrame(de_rows),
        "sample_metadata": metadata,
        "arrayed_validation": validation,
        "polarization_coefficients": coefficients,
    }


def test_source_audit_passes_and_blocks_schema_drift() -> None:
    tables = tiny_tables()
    audit = audit_source_tables(tables)
    assert audit["status"] == "passed"
    assert audit["source"]["pinned_commit"] == PINNED_COMMIT
    assert audit["checks"]["all_validation_donors_have_ntc"] is True

    broken = tables | {"de_stats": tables["de_stats"].drop(columns="crossguide_correlation")}
    with pytest.raises(SourceSchemaError, match="crossguide_correlation"):
        audit_source_tables(broken)


def test_source_audit_blocks_duplicate_keys_and_unmatched_controls() -> None:
    tables = tiny_tables()
    duplicate = pd.concat([tables["de_stats"], tables["de_stats"].iloc[[0]]], ignore_index=True)
    with pytest.raises(SourceSchemaError, match="duplicate"):
        audit_source_tables(tables | {"de_stats": duplicate})

    no_control = tables["arrayed_validation"].query("Perturbation != 'NTC'")
    with pytest.raises(SourceSchemaError, match="lacks an NTC"):
        audit_source_tables(tables | {"arrayed_validation": no_control})


def test_downloader_verifies_new_and_cached_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tcell_perturbseq import sources

    payload = b"a,b\n1,2\n"
    digest = hashlib.sha256(payload).hexdigest()
    spec = SourceSpec(
        key="tiny",
        filename="tiny.csv",
        relative_path="metadata/tiny.csv",
        expected_bytes=len(payload),
        expected_sha256=digest,
        required_columns=("a", "b"),
    )
    monkeypatch.setattr(sources, "SOURCE_SPECS", (spec,))
    monkeypatch.setattr(
        sources.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(payload)
    )

    paths = download_sources(tmp_path)
    assert paths["tiny"].read_bytes() == payload
    assert download_sources(tmp_path)["tiny"] == paths["tiny"]

    paths["tiny"].write_bytes(b"stale")
    with pytest.raises(OSError, match="Checksum mismatch"):
        download_sources(tmp_path)


def test_cli_contract_uses_public_command_and_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "all",
            "--data-dir",
            "inputs",
            "--output-dir",
            "results",
            "--top-n",
            "7",
            "--min-cells-target",
            "120",
            "--force",
        ]
    )
    assert parser.prog == "perturbseq-triage"
    assert args.command == "all"
    assert args.data_dir == Path("inputs")
    assert args.output_dir == Path("results")
    assert args.top_n == 7
    assert args.min_cells_target == 120
    assert args.force is True


def test_tiny_frames_write_all_tables_figures_and_reports(tmp_path: Path) -> None:
    config = AnalysisConfig(data_dir=tmp_path / "data", output_dir=tmp_path / "output", top_n=2)
    tables = tiny_tables()
    audit = audit_source_tables(tables)
    results = analyze_tables(tables, config)

    table_paths = write_result_tables(results, config.output_dir)
    figure_paths = write_figures(results, config)
    audit_path = write_source_audit(audit, config.output_dir)
    report_path = write_report(results, config, audit)
    methods_path = write_methods(config)

    assert len(table_paths) == 9
    assert len(figure_paths) == 4
    for path in [*table_paths, *figure_paths, audit_path, report_path, methods_path]:
        assert path.is_file()
        assert path.stat().st_size > 0
    assert "not experimental verification" in report_path.read_text(encoding="utf-8")
    assert "No p-values" in methods_path.read_text(encoding="utf-8")


def test_manifest_records_timestamp_commit_and_hashes(tmp_path: Path) -> None:
    config = AnalysisConfig(data_dir=tmp_path / "data", output_dir=tmp_path / "output")
    config.data_dir.mkdir(parents=True)
    config.output_dir.mkdir(parents=True)
    for spec in SOURCE_SPECS:
        (config.data_dir / spec.filename).write_text(spec.key, encoding="utf-8")
    artifact = config.output_dir / "artifact.txt"
    artifact.write_text("result", encoding="utf-8")
    audit = {"status": "passed"}

    path = write_manifest(config, audit, [artifact])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["pinned_commit"] == PINNED_COMMIT
    assert payload["generated_at_utc"].endswith("+00:00")
    assert len(payload["source_files"]) == 4
    assert payload["artifacts"][0]["sha256"] == hashlib.sha256(b"result").hexdigest()
