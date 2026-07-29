"""Plain-language reports and provenance for a completed analysis run."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pandas as pd

from tcell_exhaustion.config import AnalysisConfig
from tcell_exhaustion.data import InputAudit


def sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    """Return a streaming SHA-256 digest for an input or output artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def package_versions() -> dict[str, str]:
    """Capture the packages that materially affect the numerical result."""

    names = [
        "verified-tcell-exhaustion-triage",
        "python",
        "anndata",
        "scanpy",
        "numpy",
        "pandas",
        "scipy",
        "pydeseq2",
        "igraph",
        "leidenalg",
        "matplotlib",
        "seaborn",
    ]
    result: dict[str, str] = {}
    for name in names:
        if name == "python":
            import platform

            result[name] = platform.python_version()
            continue
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "not-installed"
    return result


def write_methods(
    path: Path,
    config: AnalysisConfig,
    audit: InputAudit,
    *,
    primary_resolution: float,
) -> Path:
    """Write a concise methods section that reflects actual configured choices."""

    marker_text = "; ".join(
        f"{name}: {', '.join(genes)}" for name, genes in config.marker_panels.as_dict().items()
    )
    content = f"""# Methods

## Analysis contract

This run used the pre-registered CD8 gate `(CD8A > 0 OR CD8B > 0) AND CD4 == 0` on raw counts.
The condition contrast was **{config.condition_b} versus {config.condition_a}**. The input audit
selected the **{audit.branch.value}** branch. Raw counts came only from
`layers[{config.counts_layer!r}]`; normalized values were never summed for pseudobulk inference.

## Quality control and representation

Cells were required to have {config.qc.min_genes}–{config.qc.max_genes} detected genes and no more
than {config.qc.max_mito_pct:g}% mitochondrial counts. Passing CD8+ cells were library-size
normalized to 10,000 counts and log-transformed for gene-set scoring and visualization. PCA used
up to 2,000 variable genes; a fixed random seed ({config.seed}) was used for neighbors, UMAP, and
Leiden. UMAP is a visualization, not statistical evidence.

## Annotation and exhaustion score

Clusters were labeled from pre-registered marker scores ({marker_text}). The operational
effector-memory positive markers were {', '.join(config.effector_memory_rule.positive)} (at least
{config.effector_memory_rule.min_positive} above their dataset-wide means), with
{', '.join(config.effector_memory_rule.negative)} used as a negative-marker score penalty. The
exhaustion
module was {', '.join(config.exhaustion_genes)} and used Scanpy control-gene binning. The primary
Leiden resolution was {primary_resolution:g}; robustness was checked at
{', '.join(str(value) for value in config.resolutions)}.

## Statistical inference

Module scores were first averaged per donor × subtype, then compared between conditions using a
two-sided donor-level Welch test; FDR was controlled across subtype tests with Benjamini–Hochberg.
For the headline subtype, raw counts were summed per donor × condition and modeled with PyDESeq2
(condition-only design for donors nested in condition; donor + condition for repeated donors).
FDR was controlled across all tested genes. A log-CPM donor-level Welch analysis was also saved as
a transparent sensitivity calculation. Per-cell Mann–Whitney differential expression was
exploratory and used only to demonstrate pseudoreplication.

## Verification boundary

A per-cell hit can be called **verified** only when it has the same effect direction and
pseudobulk FDR < 0.05 **and** a human-auditable PubMed/Open Targets evidence record explicitly
passes. “Verified” here means computationally corroborated and prioritized. It does not mean
wet-lab validated.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_report(
    path: Path,
    *,
    config: AnalysisConfig,
    audit: InputAudit,
    headline: dict[str, Any],
    donor_stats: pd.DataFrame,
    robustness: pd.DataFrame,
    reviewer: pd.DataFrame | None,
    simulated: bool,
) -> Path:
    """Write a result-first report with honest conditional wording."""

    subtype = headline.get("subtype", "not identified")
    delta = headline.get("delta")
    q_value = headline.get("p_adj")
    significant = bool(headline.get("significant", False))
    robust = bool(robustness["robust"].all()) if not robustness.empty else False
    verified_count = (
        int(reviewer["final_status"].eq("VERIFIED").sum())
        if reviewer is not None and "final_status" in reviewer
        else 0
    )
    survives_count = (
        int(reviewer["status"].eq("SURVIVES").sum())
        if reviewer is not None and "status" in reviewer
        else 0
    )
    reviewed_count = len(reviewer) if reviewer is not None else 0
    demo_banner = (
        "> **SIMULATED DEMO — NOT BIOLOGICAL EVIDENCE.** This report proves the workflow, not a\n"
        "> claim about patients, disease, or treatment.\n\n"
        if simulated
        else ""
    )

    if significant and delta is not None and q_value is not None:
        claim = (
            f"The largest positive donor-level exhaustion-score shift was in "
            f"**{subtype}** (B − A = {float(delta):.3f}, FDR = {float(q_value):.3g})."
        )
        claim += (
            " The direction and FDR criterion held across every registered resolution."
            if robust
            else " The registered resolution sweep did not support a fully robust claim."
        )
    else:
        claim = (
            "No subtype met the pre-registered positive-direction and FDR < 0.05 headline rule. "
            "The correct result is therefore an inconclusive/null finding, not a selected hit."
        )

    branch_note = {
        "donor_aware": (
            "Donors were available, so donor-level inference and the reviewer loop were enabled."
        ),
        "exploratory_no_donor": (
            "No usable donor labels were available; all inferential output is exploratory."
        ),
        "marker_fallback": (
            "Only one condition was available; subtype patterns are descriptive because a "
            "marker-defined contrast can be circular."
        ),
        "blocked": "Input validation blocked the analysis.",
    }[audit.branch.value]

    content = f"""# Verified CD8+ T-cell Exhaustion Triage — Run Report

{demo_banner}## Answer first

{claim}

The reviewer audited {reviewed_count} fast per-cell hits: {survives_count} survived donor-level
recomputation and {verified_count} also had explicit external-evidence approval. A surviving
statistical hit without reviewed external evidence is **not verified**.

## What was analyzed

- Input: `{config.input_path}`
- Cells / genes before filtering: {audit.n_cells:,} / {audit.n_genes:,}
- Contrast: {config.condition_b} versus {config.condition_a}
- Statistical branch: `{audit.branch.value}` — {branch_note}
- Required genes missing: {', '.join(audit.missing_genes) if audit.missing_genes else 'none'}

## How to read the deliverables

1. **Annotated UMAP:** local neighbors with similar expression should group, and labels should be
   supported by markers. UMAP spacing is not an effect size or a p-value.
2. **Exhaustion violin:** the translucent shape shows cells; overlaid points show donor means.
   The donor count—not the cell count—is the independent sample size.
3. **Volcano:** rightward genes increase in B; height is donor-level FDR evidence. Red points are
   the pre-registered exhaustion panel, but FDR was corrected across every tested gene.
4. **Robustness table:** a claim is robust only when its direction and FDR criterion survive all
   four pre-registered Leiden resolutions.
5. **Reviewer table:** `SURVIVES` means the fast cell-level hit agrees with donor pseudobulk;
   `VERIFIED` additionally requires reviewed PubMed/Open Targets evidence.

## Headline subtype table

{donor_stats.to_markdown(index=False) if not donor_stats.empty else 'No testable subtype rows.'}

## Resolution robustness

{robustness.to_markdown(index=False) if not robustness.empty else 'Not available for this branch.'}

## Limitations

- This is observational RNA evidence and cannot establish causality or therapeutic benefit.
- In-silico corroboration is not qPCR, flow cytometry, or functional-assay validation.
- RNA dropout makes the CD8/CD4 gate imperfect; expert annotations should be compared when present.
- Marker-based subtype labels and module scores depend on the registered panels and data quality.
- Batch, tissue, treatment, and donor composition can confound a condition contrast.
- Literature presence is context-dependent plausibility, not proof that a gene drives this dataset.

See `methods.md`, `provenance/manifest.json`, and the teaching notebook for the exact workflow.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_walkthrough_script(
    path: Path,
    *,
    headline: dict[str, Any],
    robustness: pd.DataFrame,
    reviewer: pd.DataFrame | None,
    simulated: bool,
) -> Path:
    """Create a truthful three-minute demo script the learner can personalize."""

    subtype = headline.get("subtype", "no qualifying subtype")
    delta = headline.get("delta")
    q_value = headline.get("p_adj")
    robust = bool(robustness["robust"].all()) if not robustness.empty else False
    failures = (
        int(reviewer["status"].ne("SURVIVES").sum())
        if reviewer is not None and "status" in reviewer
        else 0
    )
    demo_note = (
        "This is simulated teaching data, so none of the biology shown is a real discovery. "
        if simulated
        else ""
    )
    result_phrase = (
        f"{subtype}, with a donor-mean score change of {float(delta):.3f} "
        f"and FDR {float(q_value):.3g}"
        if delta is not None and q_value is not None
        else "no subtype that passed the registered headline rule"
    )
    content = f"""# Three-minute walkthrough script

**0:00–0:25 — The decision problem**

“This project helps a scientist decide which computational hits deserve expensive follow-up.
{demo_note}The key promise is not automated biological validation. It is an auditable separation
between
a fast cell-level signal and a stricter donor-level recomputation.”

**0:25–0:55 — Input and guardrails**

“I preserved raw integer counts, locked the CD8 gate and six-gene exhaustion panel before looking
at results, and treated donors—not individual cells—as biological replicates. Normalized values
were used only for visualization and module scoring.”

**0:55–1:25 — UMAP and annotation**

“The first figure shows marker-defined CD8 states. UMAP is a map of local expression similarity,
not proof of cell types. I checked that each label is supported by its registered marker panel.”

**1:25–1:55 — Headline score result**

“After averaging the exhaustion score per donor and subtype, the result was {result_phrase}.
The robustness result was {
        'stable at every registered resolution'
        if robust
        else 'not stable at every registered resolution'
    },
so I {'retain' if robust else 'qualify'} the headline claim.”

**1:55–2:30 — Gene-level recomputation**

“The volcano uses counts summed per donor and a count-aware PyDESeq2 model. The reviewer then took
the naive per-cell hits and asked whether their direction and FDR survived pseudobulk. {failures}
audited hits did not survive; that difference is the pseudoreplication lesson.”

**2:30–3:00 — Boundary and takeaway**

“A hit is only labeled verified here when donor-level statistics agree and a human-auditable
PubMed/Open Targets record passes. Even then, verified means computationally corroborated—not
wet-lab validated. The reusable pattern is to aggregate to the true unit of independence and let
an independent recomputation overturn the fast first pass.”
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_manifest(
    path: Path,
    *,
    config: AnalysisConfig,
    artifacts: list[Path],
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write checksums, versions, config, and result metadata as JSON."""

    root = config.output_dir.resolve()
    artifact_rows = []
    for artifact in sorted({item.resolve() for item in artifacts if item.is_file()}):
        try:
            name = str(artifact.relative_to(root))
        except ValueError:
            name = str(artifact)
        artifact_rows.append(
            {
                "path": name.replace("\\", "/"),
                "sha256": sha256_file(artifact),
                "bytes": artifact.stat().st_size,
            }
        )
    payload: dict[str, Any] = {
        "analysis_contract": config.to_dict(),
        "input_sha256": sha256_file(config.input_path),
        "package_versions": package_versions(),
        "artifacts": artifact_rows,
    }
    if extra:
        payload["result_summary"] = extra
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path
