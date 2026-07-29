# Official dataset guide

## Dataset identity

This project uses the T-cell dataset linked by the
[Built with Claude: Life Sciences event](https://cerebralvalley.ai/e/built-with-claude-life-sciences):

**Primary Human CD4+ T Cell Perturb-seq, version 1.0**

- [Virtual Cells Platform dataset card](https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq)
- [Authors' data-sharing README](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/data_sharing_readme.md)
- [Authors' analysis repository](https://github.com/emdann/GWT_perturbseq_analysis_2025)
- Public S3 prefix: `s3://genome-scale-tcell-perturb-seq/marson2025_data/`
- [Public S3 object listing](https://genome-scale-tcell-perturb-seq.s3.amazonaws.com/?list-type=2&prefix=marson2025_data/)

The dataset card describes single-cell RNA sequencing from a genome-scale CRISPRi screen in
primary human CD4+ T cells. It reports approximately 22 million cells, four donors, and three
culture conditions: `Rest`, `Stim8hr`, and `Stim48hr`. Version 1.0 was released on December 22,
2025 under the MIT License. The card states that the dataset contains no personally identifying
information.

This is **not** a CD8+ T-cell exhaustion dataset. The earlier CD8+ dataset in this repository is a
deterministic synthetic teaching fixture and must not be confused with the official source.

## Scale and storage decision

The public S3 listing reports 12 cell-level files, one per donor-condition combination. Their
combined size is:

```text
1,735,835,115,866 bytes
= approximately 1.58 TiB
= approximately 1.74 decimal TB
```

Other matrix artifacts are also large:

| Artifact | Public object size | Approximate binary size | Contents |
|---|---:|---:|---|
| 12 `D*_*.assigned_guide.h5ad` files combined | 1,735,835,115,866 bytes | 1.58 TiB | Cell-level sparse UMI counts and guide assignments. |
| `GWCD4i.pseudobulk_merged.h5ad` | 44,566,657,140 bytes | 41.5 GiB | Guide × donor × condition summed UMI counts across 18,129 genes. |
| `GWCD4i.DE_stats.h5ad` | 16,786,240,107 bytes | 15.6 GiB | Per-target, per-condition DE matrices. |
| `GWCD4i.DE_stats.by_donors.h5mu` | 16,866,278,447 bytes | 15.7 GiB | Author-computed donor-pair DE results. |
| `GWCD4i.DE_stats.by_guide.h5mu` | 29,424,424,894 bytes | 27.4 GiB | Author-computed guide-level DE results. |

Those files are valuable for a full independent reanalysis, but they are not required for this
learning project. Downloading them would add large storage and compute requirements without
changing the summary-level question.

The primary workflow therefore uses public CSV summaries totaling only a few megabytes. That
choice is part of the claim boundary: the project audits and ranks source-reported results rather
than independently refitting them.

## Summary inputs used here

### 1. Perturbation-condition DE summary

Filename: `DE_stats.suppl_table.csv`

- [GitHub file](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/suppl_tables/DE_stats.suppl_table.csv)
- [Direct public S3 file](https://genome-scale-tcell-perturb-seq.s3.amazonaws.com/marson2025_data/suppl_tables/DE_stats.suppl_table.csv)

The GitHub table currently has 33,983 data rows. Each row represents a target perturbation in one
of the three culture conditions. Fields used by this workflow are:

| Column | Meaning in the source table | Use in this project |
|---|---|---|
| `target_contrast_gene_name` | Perturbed target gene symbol. | Candidate identifier. |
| `culture_condition` | `Rest`, `Stim8hr`, or `Stim48hr`. | Ranking stratum. |
| `n_cells_target` | Number of targeted cells supporting the result. | Require at least 100. |
| `ontarget_effect_size` | Estimated effect on the intended target. | Require a negative value for CRISPRi direction. |
| `ontarget_significant` | Source on-target significance flag at 10% FDR. | Require `True`. |
| `offtarget_flag` | Source flag for a potential off-target concern. | Require `False`. |
| `n_downstream` | Source count of significant downstream genes, excluding the intended target. | Within-condition ranking component. |
| `crossdonor_correlation_min` | Minimum source-reported cross-donor correlation. | Require present and positive; then rank. |
| `crossguide_correlation` | Source-reported correlation between guide-specific responses. | Require present and positive; then rank. |

The table's `n_downstream` value is based on the authors' 10% FDR discoveries. It is
power- and cell-count-dependent, not an effect size. A perturbation with more downstream
discoveries is not necessarily stronger, safer, more specific, or more therapeutically useful.

The correlation fields are summaries produced by the authors from larger artifacts. This project
does not recalculate them. Requiring positive values is a transparent source-QC gate, not an
independent replication.

### 2. Sample metadata

Filename: `sample_metadata.suppl_table.csv`

- [GitHub file](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/suppl_tables/sample_metadata.suppl_table.csv)
- [Direct public S3 file](https://genome-scale-tcell-perturb-seq.s3.amazonaws.com/marson2025_data/suppl_tables/sample_metadata.suppl_table.csv)

The table contains 12 donor-condition rows: four donors across the three conditions. Relevant
fields include `donor_id`, `culture_condition`, `10xrun_id`, `library_id`, and sequencing metadata.
The workflow uses it to audit study structure, not to fit a new donor-level model.

Keep `10xrun_id` visible when interpreting condition patterns. The summary workflow consumes the
authors' estimates and does not independently model all run/batch effects.

### 3. Polarization prediction coefficients

Filename: `polarization_prediction_condition_comparison_regulator_coefficients.csv`

- [GitHub file](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/suppl_tables/polarization_prediction_condition_comparison_regulator_coefficients.csv)

The current table has 23,172 rows of coefficients from the authors' activation and polarization
prediction analyses. Fields include `coef_mean`, `coef_sem`, `coef_rank`, `regulator`,
`known_regulators`, `dataset_key`, `regulator_type`, `celltype`, and `signature`.

The workflow selects rows whose regulator is a source-QC-pass gene and adds flags for membership in
the per-condition top lists and cross-condition candidate set. This is descriptive annotation. The
pipeline does not refit the authors' model or independently validate a polarization effect.

### 4. Arrayed IL-10/IL-21 follow-up

Filename: `IL10_IL21_arrayed_validation.csv`

- [GitHub file](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/suppl_tables/IL10_IL21_arrayed_validation.csv)

The current table has 53 rows, six follow-up donors, nine selected perturbations, and
non-targeting-control rows labeled `NTC`, `NTC1`, `NTC2`, or `NTC3`. It reports `IL10_perc` and
`IL21_perc` values.

The workflow subtracts each donor's mean available NTC value from that donor's perturbation value
for each cytokine. It does not fill missing donor-perturbation pairs and does not run a confirmatory
hypothesis test. Results are descriptive author-provided follow-up, not independent validation.

## Reproducible source URLs

The repository's contract is recorded in
[`configs/official_cd4.yaml`](../configs/official_cd4.yaml). The public discovery locations are:

```text
s3://genome-scale-tcell-perturb-seq/marson2025_data/
https://github.com/emdann/GWT_perturbseq_analysis_2025/tree/master/metadata/suppl_tables
```

For reproducible downloads, prefer a commit-pinned GitHub raw URL and record the local file hash.
The pinned source revision in the configuration can be compared with the authors' current `master`
branch before a future rerun. A moving branch may legitimately change after this project is
released.

If using the Virtual Cells Platform CLI for discovery:

```powershell
vcp data search "Primary Human CD4+ T Cell Perturb-seq" --exact
```

Anonymous AWS CLI access to a specific public object follows this pattern:

```powershell
aws s3 cp s3://genome-scale-tcell-perturb-seq/marson2025_data/suppl_tables/DE_stats.suppl_table.csv data/official/DE_stats.suppl_table.csv --no-sign-request
```

The project CLI handles the summary inputs, so neither external command is required for the normal
run.

## Full-artifact schemas for future work

These are documented here so you can recognize what a future extension would require.

### Cell-level `.h5ad`

Each observation is a cell. `.X` contains sparse UMI counts. Important observation fields include
`lane_id`, `n_genes_by_counts`, `total_counts`, `pct_counts_mt`, `guide_id`,
`perturbed_gene_name`, `guide_type`, `guide_group`, and `low_quality`. The variables include gene
IDs, gene names, and mitochondrial-gene flags.

### Pseudobulk `.h5ad`

Each observation aggregates a guide, donor, and culture condition. `.X` contains summed UMI
counts. Important fields include `donor_id`, `culture_condition`, `guide_id`, `n_cells`,
`total_counts`, and several `keep_*` QC fields.

### DE `.h5ad` and `.h5mu`

The main DE artifact contains log fold changes, p-values, adjusted p-values, base means, standard
errors, and z-scores across measured genes. The donor-pair and guide-level MuData files contain
author-computed stratified estimates. A true independent recomputation would need to load these or
the underlying counts, define a statistical model, handle donor and batch structure, and validate
its implementation.

## What the summary route can claim

It can claim that a row:

- is present in the official source table;
- passes the registered gates applied by this project;
- has positive author-reported donor and guide concordance;
- ranks highly relative to other eligible rows in the same condition;
- is a source-QC candidate for expert review; if it passes every gate in all three conditions, it
  can be labeled a reproducible candidate by this workflow's explicit convention.

It cannot claim that the row:

- was independently recomputed from raw counts here;
- is statistically stronger in one condition without an interaction test;
- has a larger biological effect because it has more downstream discoveries;
- is free of all off-target activity;
- generalizes beyond the four screen donors;
- is a validated drug target or treatment.

## Known analysis limitations

1. Summary statistics constrain which diagnostics and alternative models are possible.
2. The source uses 10% FDR for reported discovery flags/counts.
3. Cell counts and expression levels affect discovery power.
4. Only four donors contribute to the main screen.
5. Missing cross-donor or cross-guide correlations may mean "not tested," not "biologically
   irreproducible"; this project still excludes them because reproducibility evidence is required
   for eligibility.
6. A positive correlation can be weak; ranking retains its magnitude, but the gate itself is only
   `> 0`.
7. An unflagged row is not guaranteed to lack off-target effects.
8. Condition-specific percentile ranks are relative to different eligible sets.
9. Cross-condition comparisons are descriptive because no perturbation-by-condition interaction
   model is fitted.
10. The IL-10/IL-21 follow-up has selected targets, uneven donor coverage, and no confirmatory model
    in this workflow.

These limitations are not footnotes to hide. They define the correct strength of the final claim.
