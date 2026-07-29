"""CLI for downloading and analyzing the official lightweight CD4 dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tcell_perturbseq.analysis import analyze_tables
from tcell_perturbseq.config import AnalysisConfig
from tcell_perturbseq.plotting import write_figures
from tcell_perturbseq.reporting import (
    write_manifest,
    write_methods,
    write_report,
    write_result_tables,
    write_source_audit,
)
from tcell_perturbseq.sources import (
    SOURCE_SPECS,
    audit_source_tables,
    download_sources,
    load_source_tables,
    sha256_file,
)


def _add_data_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/official_cd4_perturbseq"),
        help="directory containing the four pinned official CSVs",
    )


def _add_analysis_args(parser: argparse.ArgumentParser) -> None:
    _add_data_dir(parser)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/official_cd4_perturbseq"),
        help="directory for tables, figures, report, methods, and provenance",
    )
    parser.add_argument("--top-n", type=int, default=15, help="candidates retained per condition")
    parser.add_argument(
        "--min-cells-target",
        type=int,
        default=100,
        help="minimum source n_cells_target hard gate (default: 100)",
    )


def _add_download_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing source files after downloading and checksum verification",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="network timeout for each pinned CSV",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the public argument parser (also useful for no-network tests)."""

    parser = argparse.ArgumentParser(
        prog="perturbseq-triage",
        description=(
            "Lightweight, source-audited triage of the official CD4+ T-cell Perturb-seq data"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="download and verify four pinned CSVs")
    _add_data_dir(download)
    _add_download_args(download)

    run = subparsers.add_parser("run", help="audit downloaded CSVs and build every deliverable")
    _add_analysis_args(run)

    all_steps = subparsers.add_parser("all", help="download, audit, analyze, and report")
    _add_analysis_args(all_steps)
    _add_download_args(all_steps)
    return parser


def _analysis_config(args: argparse.Namespace) -> AnalysisConfig:
    return AnalysisConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        top_n=args.top_n,
        min_cells_target=args.min_cells_target,
    )


def _summary_payload(results: Any, config: AnalysisConfig) -> dict[str, Any]:
    pass_counts = (
        results.candidate_scores.groupby("culture_condition", sort=False)
        .size()
        .reindex(config.conditions, fill_value=0)
        .astype(int)
        .to_dict()
    )
    lead = (
        None
        if results.cross_condition_candidates.empty
        else results.cross_condition_candidates.iloc[0][
            ["gene", "min_priority_score", "worst_condition"]
        ].to_dict()
    )
    return {
        "status": "complete",
        "source_qc_passes_by_condition": pass_counts,
        "cross_condition_candidate_count": int(len(results.cross_condition_candidates)),
        "lead_cross_condition_candidate": lead,
        "output_dir": str(config.output_dir.resolve()),
    }


def run_analysis(config: AnalysisConfig) -> dict[str, Any]:
    """Audit the pinned inputs, run the analysis, and write every registered artifact."""

    tables = load_source_tables(config.data_dir, verify_hashes=True)
    audit = audit_source_tables(tables, conditions=config.conditions)
    results = analyze_tables(tables, config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[Path] = []
    artifacts.extend(write_result_tables(results, config.output_dir))
    artifacts.extend(write_figures(results, config))
    artifacts.append(write_source_audit(audit, config.output_dir))
    artifacts.append(write_report(results, config, audit))
    artifacts.append(write_methods(config))

    summary = _summary_payload(results, config)
    summary_path = config.output_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    artifacts.append(summary_path)
    manifest = write_manifest(config, audit, artifacts)
    summary["manifest"] = str(manifest.resolve())
    return summary


def _download_payload(paths: dict[str, Path]) -> dict[str, Any]:
    spec_lookup = {spec.key: spec for spec in SOURCE_SPECS}
    return {
        "status": "downloaded_and_verified",
        "files": {
            key: {
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "url": spec_lookup[key].url,
            }
            for key, path in paths.items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Execute ``perturbseq-triage`` and return its process status."""

    args = build_parser().parse_args(argv)
    if args.command == "download":
        paths = download_sources(
            args.data_dir,
            force=args.force,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(_download_payload(paths), indent=2))
        return 0
    if args.command == "run":
        print(json.dumps(run_analysis(_analysis_config(args)), indent=2))
        return 0
    if args.command == "all":
        download_sources(
            args.data_dir,
            force=args.force,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(run_analysis(_analysis_config(args)), indent=2))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
