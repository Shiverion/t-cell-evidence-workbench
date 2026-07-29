"""Tables, plain-language interpretation, methods, and provenance artifacts."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pandas as pd

from tcell_perturbseq.analysis import AnalysisResults
from tcell_perturbseq.config import AnalysisConfig
from tcell_perturbseq.sources import PINNED_COMMIT, REPOSITORY_URL, SOURCE_SPECS, sha256_file


def write_result_tables(results: AnalysisResults, output_dir: Path) -> list[Path]:
    """Write every analysis table under stable, tutorial-friendly names."""

    table_dir = Path(output_dir) / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, frame in results.tables().items():
        path = table_dir / f"{name}.csv"
        frame.to_csv(path, index=False, float_format="%.10g")
        paths.append(path)
    return paths


def write_source_audit(audit: dict[str, Any], output_dir: Path) -> Path:
    """Persist the blocking schema audit next to the provenance manifest."""

    path = Path(output_dir) / "provenance" / "source_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _markdown_table(frame: pd.DataFrame, columns: list[str], *, rows: int = 12) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows met this criterion."
    return frame.loc[:, available].head(rows).to_markdown(index=False, floatfmt=".3f")


def write_report(
    results: AnalysisResults,
    config: AnalysisConfig,
    audit: dict[str, Any],
) -> Path:
    """Write a result-first report while preserving the inference boundary."""

    path = config.output_dir / "report.md"
    final_counts = (
        results.filter_funnel.sort_values("stage_order")
        .groupby("culture_condition", sort=False)
        .tail(1)
        .set_index("culture_condition")["n_rows"]
        .to_dict()
    )
    cross = results.cross_condition_candidates
    if cross.empty:
        answer = (
            "No gene passed every hard gate in all three culture conditions. The appropriate "
            "output is therefore a condition-specific shortlist, not a cross-condition claim."
        )
    else:
        lead = cross.iloc[0]
        answer = (
            f"**{lead['gene']}** had the highest worst-condition priority score "
            f"({float(lead['min_priority_score']):.3f}) among genes that passed source QC in "
            "Rest, Stim8hr, and Stim48hr. This is a descriptive prioritization result, not "
            "experimental verification."
        )
    top_table = _markdown_table(
        results.top_candidates_by_condition,
        [
            "culture_condition",
            "rank_within_condition",
            "gene",
            "n_downstream",
            "crossdonor_min",
            "crossguide",
            "priority_score",
        ],
        rows=config.top_n * len(config.conditions),
    )
    cross_table = _markdown_table(
        cross,
        [
            "cross_condition_rank",
            "gene",
            "Rest_priority_score",
            "Stim8hr_priority_score",
            "Stim48hr_priority_score",
            "min_priority_score",
            "worst_condition",
        ],
    )
    validation_table = _markdown_table(
        results.validation_summary,
        [
            "perturbation",
            "n_donors",
            "IL10_mean_delta",
            "IL10_median_delta",
            "IL21_mean_delta",
            "IL21_median_delta",
        ],
        rows=50,
    )
    pass_text = ", ".join(
        f"{condition}: {int(final_counts.get(condition, 0)):,}" for condition in config.conditions
    )
    content = f"""# Official CD4+ T-cell Perturb-seq Candidate Triage

## Answer first

{answer}

The final source-QC pass counts were {pass_text}. A **source-QC pass** means a row met the declared
on-target, off-target, cell-count, cross-donor, and cross-guide gates. A **reproducible candidate**
means it passed those source gates in all three conditions. Neither label means wet-lab validated,
causal, safe, or therapeutically useful.

## Data actually used

This run used four small official supplementary CSVs from [{REPOSITORY_URL}]({REPOSITORY_URL}) at
commit `{PINNED_COMMIT}`. It did **not** download or analyze the 22-million-cell matrices. The
source audit passed for {audit["design"]["screen_samples"]} screen samples and
{len(audit["design"]["screen_donors"])} screen donors across Rest, Stim8hr, and Stim48hr.

## Top candidates within each condition

{top_table}

## Candidates passing all three conditions

{cross_table}

The cross-condition score is the minimum of the three condition-specific priority scores. This
conservative aggregation rewards a strong weakest condition, but it is **not** a formal
condition-by-perturbation interaction test. Differences between conditions are descriptive.

## Arrayed IL10/IL21 follow-up

{validation_table}

Each delta subtracts the mean of that donor's available NTC, NTC1, NTC2, and NTC3 measurements.
Only descriptive donor-level summaries are shown; no inferential p-values were calculated. The
official source file calls this an arrayed validation experiment, but this report uses the more
limited term **arrayed follow-up** and does not turn a descriptive delta into a validation claim.

## How the priority score should be read

- `n_downstream` is the authors' number of downstream discoveries at 10% FDR. It is sensitive to
  statistical power and cell count and is **not an effect size**.
- `crossdonor_min` and `crossguide` are correlations reported by the source authors. This
  lightweight workflow filters and ranks them; it does not independently recompute them.
- Each metric is percentile-ranked within condition. Their geometric mean is a triage heuristic,
  not a calibrated probability of biological truth.
- The polarization coefficient table is retained only as an official descriptive annotation. It
  is not an extra independent validation layer.

## Deliverables

See `tables/` for all decisions and scores, `figures/` for the four teaching figures,
`methods.md` for the exact contract, and `provenance/manifest.json` for pinned URLs and hashes.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_methods(config: AnalysisConfig) -> Path:
    """Write the exact deterministic analysis contract in prose and formulas."""

    path = config.output_dir / "methods.md"
    content = f"""# Methods — Official CD4+ T-cell Perturb-seq Lightweight Triage

## Source and scope

Four supplementary CSVs were downloaded from the authors' GitHub repository at immutable commit
`{PINNED_COMMIT}`. Expected byte sizes and SHA-256 hashes were checked before analysis. This
workflow uses published summary tables; it does not reprocess cell-level counts, rerun DESeq2, or
independently recompute cross-donor/cross-guide correlations.

## Blocking source audit

Required columns, numeric parsing, boolean parsing, unique perturbation-condition keys, unique
sample identifiers, presence of Rest/Stim8hr/Stim48hr, and a matched NTC-family control for every
arrayed donor were checked before scoring. A failed audit stops the run.

## Hard gates

A perturbation-condition row was labeled `source-QC pass` only when every criterion held:

1. `ontarget_significant == True` (the source authors' 10% FDR call),
2. `ontarget_effect_size < 0` (direction consistent with CRISPR interference knockdown),
3. `offtarget_flag == False`,
4. `n_cells_target >= {config.min_cells_target}`,
5. `crossdonor_correlation_min` was present and greater than zero, and
6. `crossguide_correlation` was present and greater than zero.

All pass/fail flags and failure reasons were retained in `tables/source_qc_decisions.csv`.

## Within-condition priority score

Among source-QC passes, `n_downstream`, `crossdonor_correlation_min`, and
`crossguide_correlation` were separately converted to average percentile ranks within each culture
condition using `rank(method="average", pct=True)`. The output columns are
`n_downstream_percentile`, `crossdonor_min_percentile`, and `crossguide_percentile`.

`priority_score = (n_downstream_percentile × crossdonor_min_percentile ×
crossguide_percentile)^(1/3)`

The geometric mean requires balanced performance: one weak component lowers the result. It does
not make the source metrics independent, and it is not a posterior probability or effect size.
`n_downstream` is the source authors' count of 10%-FDR downstream discoveries and depends on power
and cell count.

## Cross-condition ranking

Only genes with a source-QC pass in all three conditions were eligible. Their cross-condition
score was `min(Rest_priority_score, Stim8hr_priority_score, Stim48hr_priority_score)`. Genes were
ranked from largest to smallest minimum score. This is a descriptive robustness heuristic, not a
formal interaction analysis.

## Donor-matched arrayed follow-up

Within each donor, the mean IL10 and IL21 percentage among available perturbation labels exactly
matching NTC, NTC1, NTC2, or NTC3 was calculated. For each non-control sample:

`delta = observed percentage − donor mean NTC-family percentage`

Means, medians, minima, and maxima of these deltas were reported by perturbation. No p-values,
confidence intervals, or multiple-testing claims were produced because this small follow-up table
was used descriptively.

## Labels and inference boundary

`source-QC pass` and `reproducible candidate` are prioritization labels only. The workflow never
uses `verified` or `validated` as a computational conclusion. Experimental replication,
pre-specified endpoint testing, mechanism work, and safety evaluation remain outside scope.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _package_versions() -> dict[str, str]:
    packages = ("pandas", "numpy", "matplotlib")
    result = {"python": platform.python_version()}
    for package in packages:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not-installed"
    return result


def write_manifest(
    config: AnalysisConfig,
    audit: dict[str, Any],
    artifacts: list[Path],
) -> Path:
    """Record the analysis contract plus source/output checksums."""

    source_rows = []
    for spec in SOURCE_SPECS:
        path = config.data_dir / spec.filename
        source_rows.append(
            {
                "key": spec.key,
                "path": str(path.resolve()),
                "url": spec.url,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "expected_bytes": spec.expected_bytes,
                "expected_sha256": spec.expected_sha256,
            }
        )
    artifact_rows = []
    root = config.output_dir.resolve()
    for artifact in sorted({path.resolve() for path in artifacts if path.is_file()}):
        try:
            relative = artifact.relative_to(root).as_posix()
        except ValueError:
            relative = str(artifact)
        artifact_rows.append(
            {
                "path": relative,
                "bytes": artifact.stat().st_size,
                "sha256": sha256_file(artifact),
            }
        )
    payload = {
        "workflow": "official-cd4-perturbseq-lightweight-triage",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_repository": REPOSITORY_URL,
        "pinned_commit": PINNED_COMMIT,
        "analysis_contract": config.to_dict(),
        "source_audit": audit,
        "source_files": source_rows,
        "package_versions": _package_versions(),
        "artifacts": artifact_rows,
    }
    path = config.output_dir / "provenance" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
