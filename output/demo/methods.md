# Methods

## Analysis contract

This run used the pre-registered CD8 gate `(CD8A > 0 OR CD8B > 0) AND CD4 == 0` on raw counts.
The condition contrast was **B versus A**. The input audit
selected the **donor_aware** branch. Raw counts came only from
`layers['counts']`; normalized values were never summed for pseudobulk inference.

## Quality control and representation

Cells were required to have 10–500 detected genes and no more
than 20% mitochondrial counts. Passing CD8+ cells were library-size
normalized to 10,000 counts and log-transformed for gene-set scoring and visualization. PCA used
up to 2,000 variable genes; a fixed random seed (42) was used for neighbors, UMAP, and
Leiden. UMAP is a visualization, not statistical evidence.

## Annotation and exhaustion score

Clusters were labeled from pre-registered marker scores (memory_stem_like: TCF7, IL7R, SELL, CCR7; effector_cytotoxic: GZMB, PRF1, NKG7, GZMK; terminally_exhausted: TOX, PDCD1, HAVCR2, ENTPD1, LAYN). The operational
effector-memory positive markers were GZMK, NKG7, IL7R (at least
2 above their dataset-wide means), with
HAVCR2, ENTPD1 used as a negative-marker score penalty. The
exhaustion
module was PDCD1, HAVCR2, LAG3, TOX, TIGIT, ENTPD1 and used Scanpy control-gene binning. The primary
Leiden resolution was 0.6; robustness was checked at
0.4, 0.6, 0.8, 1.0.

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
