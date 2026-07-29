# Verified CD8+ T-cell Exhaustion Triage — Run Report

> **SIMULATED DEMO — NOT BIOLOGICAL EVIDENCE.** This report proves the workflow, not a
> claim about patients, disease, or treatment.

## Answer first

The largest positive donor-level exhaustion-score shift was in **terminally_exhausted** (B − A = 1.886, FDR = 0.000271). The direction and FDR criterion held across every registered resolution.

The reviewer audited 30 fast per-cell hits: 6 survived donor-level
recomputation and 6 also had explicit external-evidence approval. A surviving
statistical hit without reviewed external evidence is **not verified**.

## What was analyzed

- Input: `C:\Users\miqba\projects\claude-science-hackathon-learning-plan\data\demo_tcells.h5ad`
- Cells / genes before filtering: 648 / 118
- Contrast: B versus A
- Statistical branch: `donor_aware` — Donors were available, so donor-level inference and the reviewer loop were enabled.
- Required genes missing: none

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

| subtype              | condition_a   | condition_b   |   mean_a |   mean_b |    delta |   n_units_a |   n_units_b |   n_donors_a |   n_donors_b |   t_statistic |     p_value | donor_aware   | analysis_unit   |       p_adj | significant   | test_status     |
|:---------------------|:--------------|:--------------|---------:|---------:|---------:|------------:|------------:|-------------:|-------------:|--------------:|------------:|:--------------|:----------------|------------:|:--------------|:----------------|
| memory_stem_like     | A             | B             | -1.72103 | -1.34937 | 0.371664 |           6 |           6 |            6 |            6 |       2.24873 | 0.0497138   | True          | donor mean      | 0.066285    | False         | NOT_SIGNIFICANT |
| effector_cytotoxic   | A             | B             | -1.95344 | -1.62799 | 0.325458 |           6 |           6 |            6 |            6 |       1.37298 | 0.202678    | True          | donor mean      | 0.202678    | False         | NOT_SIGNIFICANT |
| terminally_exhausted | A             | B             |  2.15784 |  4.04415 | 1.88631  |           6 |           6 |            6 |            6 |       9.51606 | 6.78077e-05 | True          | donor mean      | 0.000271231 | True          | SIGNIFICANT     |
| effector_memory      | A             | B             | -1.60457 | -1.10736 | 0.497212 |           6 |           6 |            6 |            6 |       2.3628  | 0.0431895   | True          | donor mean      | 0.066285    | False         | NOT_SIGNIFICANT |

## Resolution robustness

|   resolution | headline_subtype     |   n_donors_a |   n_donors_b |   delta |       p_adj | matching_direction   | passes_fdr   | robust   |
|-------------:|:---------------------|-------------:|-------------:|--------:|------------:|:---------------------|:-------------|:---------|
|          0.4 | terminally_exhausted |            6 |            6 | 1.92233 | 1.16254e-05 | True                 | True         | True     |
|          0.6 | terminally_exhausted |            6 |            6 | 1.88631 | 0.000271231 | True                 | True         | True     |
|          0.8 | terminally_exhausted |            6 |            6 | 1.88631 | 0.000271231 | True                 | True         | True     |
|          1   | terminally_exhausted |            6 |            6 | 1.88631 | 0.000271231 | True                 | True         | True     |

## Limitations

- This is observational RNA evidence and cannot establish causality or therapeutic benefit.
- In-silico corroboration is not qPCR, flow cytometry, or functional-assay validation.
- RNA dropout makes the CD8/CD4 gate imperfect; expert annotations should be compared when present.
- Marker-based subtype labels and module scores depend on the registered panels and data quality.
- Batch, tissue, treatment, and donor composition can confound a condition contrast.
- Literature presence is context-dependent plausibility, not proof that a gene drives this dataset.

See `methods.md`, `provenance/manifest.json`, and the teaching notebook for the exact workflow.
