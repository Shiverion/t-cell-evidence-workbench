# Methods — Official CD4+ T-cell Perturb-seq Lightweight Triage

## Source and scope

Four supplementary CSVs were downloaded from the authors' GitHub repository at immutable commit
`848d62fc2b7027f7218d6fc5f5b0c37255dc94af`. Expected byte sizes and SHA-256 hashes were checked before analysis. This
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
4. `n_cells_target >= 100`,
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
