"""End-to-end orchestration for the verified exhaustion triage workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from tcell_exhaustion.config import AnalysisConfig
from tcell_exhaustion.data import (
    AnalysisBranch,
    DataValidationError,
    audit_input,
    get_raw_counts,
    load_h5ad,
)
from tcell_exhaustion.differential_expression import pydeseq2_de
from tcell_exhaustion.plotting import (
    plot_annotated_umap,
    plot_exhaustion_violin,
    plot_qc,
    plot_robustness_table,
    plot_volcano,
)
from tcell_exhaustion.preprocessing import (
    normalize_embed_and_cluster,
    qc_and_cd8_gate,
    score_and_annotate_subtypes,
    subtype_key_for_resolution,
)
from tcell_exhaustion.reporting import (
    write_manifest,
    write_methods,
    write_report,
    write_walkthrough_script,
)
from tcell_exhaustion.statistics import (
    build_reviewer_table,
    donor_module_statistics,
    per_cell_de,
    pseudobulk_de,
)


@dataclass(frozen=True)
class RunResult:
    """Small, notebook-friendly summary of a completed run."""

    output_dir: Path
    branch: str
    headline_subtype: str | None
    headline_significant: bool
    robust: bool
    simulated: bool
    artifacts: tuple[Path, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "branch": self.branch,
            "headline_subtype": self.headline_subtype,
            "headline_significant": self.headline_significant,
            "robust": self.robust,
            "simulated": self.simulated,
            "artifacts": [str(path) for path in self.artifacts],
        }


def _save_table(frame: pd.DataFrame, path: Path, artifacts: list[Path]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    artifacts.append(path)
    return path


def _load_evidence(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    if not path.is_file():
        raise DataValidationError(f"Evidence CSV does not exist: {path}")
    frame = pd.read_csv(path)
    if "gene" not in frame:
        raise DataValidationError("Evidence CSV must contain a 'gene' column")
    return frame


def _select_headline(module_stats: pd.DataFrame) -> dict[str, Any]:
    if module_stats.empty:
        return {"subtype": None, "delta": None, "p_adj": None, "significant": False}
    candidates = module_stats.loc[
        module_stats["subtype"].astype(str).ne("ambiguous")
        & module_stats["delta"].notna()
    ].copy()
    if candidates.empty:
        return {"subtype": None, "delta": None, "p_adj": None, "significant": False}
    passing = candidates.loc[candidates["delta"].gt(0) & candidates["p_adj"].lt(0.05)]
    chosen = (passing if not passing.empty else candidates).sort_values(
        ["delta", "p_adj"], ascending=[False, True], na_position="last"
    ).iloc[0]
    return {
        "subtype": str(chosen["subtype"]),
        "delta": float(chosen["delta"]) if pd.notna(chosen["delta"]) else None,
        "p_adj": float(chosen["p_adj"]) if pd.notna(chosen["p_adj"]) else None,
        "significant": bool(
            chosen["delta"] > 0
            and pd.notna(chosen["p_adj"])
            and chosen["p_adj"] < 0.05
        ),
    }


def _robustness_sweep(
    obs: pd.DataFrame,
    config: AnalysisConfig,
    *,
    headline: dict[str, Any],
    donor_key: str | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    headline_subtype = headline.get("subtype")
    primary_delta = headline.get("delta")
    for resolution in config.resolutions:
        subtype_key = subtype_key_for_resolution(float(resolution))
        stats = donor_module_statistics(
            obs,
            subtype_key=subtype_key,
            condition_key=config.condition_key,
            condition_a=config.condition_a,
            condition_b=config.condition_b,
            donor_key=donor_key,
        )
        selected = stats.loc[stats["subtype"].astype(str).eq(str(headline_subtype))]
        if selected.empty:
            delta = np.nan
            p_adj = np.nan
            donors_a = 0
            donors_b = 0
        else:
            row = selected.iloc[0]
            delta = float(row["delta"])
            p_adj = float(row["p_adj"]) if pd.notna(row["p_adj"]) else np.nan
            donors_a = int(row["n_donors_a"])
            donors_b = int(row["n_donors_b"])
        matching = bool(
            primary_delta is not None
            and np.isfinite(delta)
            and delta != 0
            and np.sign(delta) == np.sign(float(primary_delta))
        )
        passes = bool(np.isfinite(p_adj) and p_adj < 0.05)
        rows.append(
            {
                "resolution": float(resolution),
                "headline_subtype": headline_subtype,
                "n_donors_a": donors_a,
                "n_donors_b": donors_b,
                "delta": delta,
                "p_adj": p_adj,
                "matching_direction": matching,
                "passes_fdr": passes,
                "robust": bool(matching and passes and donor_key is not None),
            }
        )
    return pd.DataFrame(rows)


def _descriptive_robustness(config: AnalysisConfig, headline_subtype: str | None) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "resolution": list(config.resolutions),
            "headline_subtype": headline_subtype,
            "n_donors_a": 0,
            "n_donors_b": 0,
            "delta": np.nan,
            "p_adj": np.nan,
            "matching_direction": False,
            "passes_fdr": False,
            "robust": False,
        }
    )


def run_pipeline(
    config: AnalysisConfig,
    *,
    evidence_path: str | Path | None = None,
) -> RunResult:
    """Run the full workflow and write a reproducible artifact bundle."""

    output = config.output_dir.resolve()
    figures = output / "figures"
    tables = output / "tables"
    provenance = output / "provenance"
    for directory in (output, figures, tables, provenance):
        directory.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    adata = load_h5ad(config.input_path)
    audit = audit_input(adata, config)
    audit_path = provenance / "input_audit.json"
    audit_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    artifacts.append(audit_path)
    config_path = provenance / "analysis_contract.yaml"
    config_path.write_text(yaml.safe_dump(config.to_dict(), sort_keys=False), encoding="utf-8")
    artifacts.append(config_path)
    if audit.blocked:
        raise DataValidationError("Input audit blocked analysis: " + "; ".join(audit.reasons))

    simulated = bool(adata.uns.get("is_simulated", False))
    gated, qc = qc_and_cd8_gate(
        adata,
        counts_layer=config.counts_layer,
        min_genes=config.qc.min_genes,
        max_genes=config.qc.max_genes,
        max_pct_mito=config.qc.max_mito_pct,
    )
    _save_table(qc.reset_index(names="cell_id"), tables / "cell_qc_and_gate.csv", artifacts)
    artifacts.append(plot_qc(qc, figures / "01_qc.png", simulated=simulated))

    processed = normalize_embed_and_cluster(
        gated,
        counts_layer=config.counts_layer,
        resolutions=config.resolutions,
        seed=config.seed,
    )
    marker_panels = config.marker_panels.as_dict()
    marker_panels["effector_memory"] = config.effector_memory_rule.positive
    primary_resolution = 0.6 if 0.6 in config.resolutions else float(config.resolutions[0])
    processed, annotation = score_and_annotate_subtypes(
        processed,
        marker_panels=marker_panels,
        negative_marker_rules={
            "effector_memory": config.effector_memory_rule.negative,
        },
        min_positive_markers={
            "effector_memory": config.effector_memory_rule.min_positive,
        },
        exhaustion_genes=config.exhaustion_genes,
        resolutions=config.resolutions,
        primary_resolution=primary_resolution,
        seed=config.seed,
    )
    _save_table(annotation, tables / "cluster_annotation_scores.csv", artifacts)
    artifacts.append(
        plot_annotated_umap(
            processed,
            figures / "02_annotated_cd8_umap.png",
            subtype_key="subtype",
            condition_key=config.condition_key,
            simulated=simulated,
        )
    )

    evidence = _load_evidence(Path(evidence_path).resolve() if evidence_path else None)
    if evidence is not None:
        _save_table(evidence, provenance / "evidence_used.csv", artifacts)
    donor_stats = pd.DataFrame()
    robustness = _descriptive_robustness(config, None)
    reviewer: pd.DataFrame | None = None
    headline = {"subtype": None, "delta": None, "p_adj": None, "significant": False}
    de_primary = pd.DataFrame()

    if audit.branch in {AnalysisBranch.DONOR_AWARE, AnalysisBranch.EXPLORATORY_NO_DONOR}:
        donor_key = config.donor_key if audit.branch is AnalysisBranch.DONOR_AWARE else None
        donor_stats = donor_module_statistics(
            processed.obs,
            subtype_key="subtype",
            condition_key=config.condition_key,
            condition_a=config.condition_a,
            condition_b=config.condition_b,
            donor_key=donor_key,
        )
        headline = _select_headline(donor_stats)
        robustness = _robustness_sweep(
            processed.obs,
            config,
            headline=headline,
            donor_key=donor_key,
        )
        _save_table(donor_stats, tables / "donor_exhaustion_statistics.csv", artifacts)
        _save_table(robustness, tables / "resolution_robustness.csv", artifacts)
        artifacts.append(
            plot_exhaustion_violin(
                processed.obs,
                donor_stats,
                figures / "03_exhaustion_violin.png",
                subtype_key="subtype",
                condition_key=config.condition_key,
                donor_key=donor_key,
                simulated=simulated,
            )
        )
        artifacts.append(
            plot_robustness_table(
                robustness,
                figures / "05_resolution_robustness.png",
                simulated=simulated,
            )
        )

        headline_subtype = headline["subtype"]
        if headline_subtype is not None:
            lognorm_log2 = processed.layers["lognorm"] / np.log(2.0)
            per_cell = per_cell_de(
                lognorm_log2,
                processed.obs,
                list(processed.var_names),
                "subtype",
                headline_subtype,
                config.condition_key,
                config.condition_a,
                config.condition_b,
            )
            _save_table(per_cell, tables / "per_cell_de_exploratory.csv", artifacts)

            if donor_key is not None:
                counts = get_raw_counts(processed, config.counts_layer)
                logcpm = pseudobulk_de(
                    counts,
                    processed.obs,
                    list(processed.var_names),
                    "subtype",
                    headline_subtype,
                    config.condition_key,
                    config.condition_a,
                    config.condition_b,
                    donor_key,
                )
                _save_table(logcpm, tables / "pseudobulk_logcpm_sensitivity.csv", artifacts)
                try:
                    de_primary, sample_info = pydeseq2_de(
                        counts,
                        processed.obs,
                        list(processed.var_names),
                        subtype_key="subtype",
                        subtype=headline_subtype,
                        condition_key=config.condition_key,
                        condition_a=config.condition_a,
                        condition_b=config.condition_b,
                        donor_key=donor_key,
                        min_donors_per_condition=config.min_donors_per_condition,
                    )
                    _save_table(sample_info, tables / "pseudobulk_sample_manifest.csv", artifacts)
                except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
                    warning_path = provenance / "pydeseq2_warning.txt"
                    warning_path.write_text(
                        "PyDESeq2 could not fit; the saved log-CPM donor test "
                        "is the declared fallback.\n"
                        + str(exc),
                        encoding="utf-8",
                    )
                    artifacts.append(warning_path)
                    de_primary = logcpm.rename(columns={"log2fc": "log2_fold_change"}).copy()
                    de_primary["method"] = "donor pseudobulk log2-CPM Welch fallback"

                _save_table(de_primary, tables / "pseudobulk_de_primary.csv", artifacts)
                reviewer = build_reviewer_table(per_cell, de_primary, evidence=evidence, top_n=30)
                _save_table(reviewer, tables / "reviewer_findings.csv", artifacts)
                plot_ready = de_primary.loc[de_primary["log2_fold_change"].notna()].copy()
                if not plot_ready.empty:
                    artifacts.append(
                        plot_volcano(
                            plot_ready,
                            figures / "04_pseudobulk_volcano.png",
                            exhaustion_genes=config.exhaustion_genes,
                            headline_subtype=headline_subtype,
                            simulated=simulated,
                        )
                    )
    else:
        descriptive = (
            processed.obs.groupby(["subtype", config.condition_key], observed=True)[
                "exhaustion_score"
            ]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        _save_table(descriptive, tables / "descriptive_exhaustion_by_subtype.csv", artifacts)
        _save_table(robustness, tables / "resolution_robustness.csv", artifacts)
        artifacts.append(
            plot_exhaustion_violin(
                processed.obs,
                donor_stats,
                figures / "03_exhaustion_violin_descriptive.png",
                subtype_key="subtype",
                condition_key=config.condition_key,
                donor_key=config.donor_key if config.donor_key in processed.obs else None,
                simulated=simulated,
            )
        )

    processed_path = output / "processed_cd8_analysis.h5ad"
    processed.write_h5ad(processed_path)
    artifacts.append(processed_path)
    methods_path = write_methods(
        output / "methods.md",
        config,
        audit,
        primary_resolution=primary_resolution,
    )
    artifacts.append(methods_path)
    report_path = write_report(
        output / "report.md",
        config=config,
        audit=audit,
        headline=headline,
        donor_stats=donor_stats,
        robustness=robustness,
        reviewer=reviewer,
        simulated=simulated,
    )
    artifacts.append(report_path)
    script_path = write_walkthrough_script(
        output / "three_minute_walkthrough.md",
        headline=headline,
        robustness=robustness,
        reviewer=reviewer,
        simulated=simulated,
    )
    artifacts.append(script_path)

    robust = bool(not robustness.empty and robustness["robust"].all())
    manifest_path = write_manifest(
        provenance / "manifest.json",
        config=config,
        artifacts=artifacts,
        extra={
            "branch": audit.branch.value,
            "headline": headline,
            "robust": robust,
            "simulated": simulated,
            "reviewer_rows": 0 if reviewer is None else len(reviewer),
        },
    )
    artifacts.append(manifest_path)
    result = RunResult(
        output_dir=output,
        branch=audit.branch.value,
        headline_subtype=headline.get("subtype"),
        headline_significant=bool(headline.get("significant", False)),
        robust=robust,
        simulated=simulated,
        artifacts=tuple(artifacts),
    )
    summary_path = output / "run_summary.json"
    summary_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return RunResult(
        output_dir=result.output_dir,
        branch=result.branch,
        headline_subtype=result.headline_subtype,
        headline_significant=result.headline_significant,
        robust=result.robust,
        simulated=result.simulated,
        artifacts=(*result.artifacts, summary_path),
    )


__all__ = ["RunResult", "run_pipeline"]
