# Project Brief: CD4+ Perturb-seq Source-QC Triage

Lab Track project for
[Built with Claude: Life Sciences](https://cerebralvalley.ai/e/built-with-claude-life-sciences),
using the recommended
[Primary Human CD4+ T Cell Perturb-seq dataset](https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq).

**One line:** turn the authors' public perturbation-level summary statistics into a transparent,
condition-specific shortlist of CRISPRi perturbations that pass on-target, coverage, off-target,
cross-donor, and cross-guide source-QC checks.

This brief supersedes the original CD8+ exhaustion proposal for the official-data submission. The
synthetic CD8+ workflow remains a legacy teaching fallback only.

## Intended user and decision

The user is a computational biologist or experimental T-cell scientist deciding which candidates
deserve a closer look before expensive independent experiments. They need to see why each row was
included, excluded, or ranked highly.

The workflow supports this narrow decision:

> Which perturbations are the most defensible **source-QC candidates** within Rest, Stim8hr, and
> Stim48hr, and which pass the same gates in all three conditions as **reproducible candidates**?

It does not discover therapeutic targets automatically. It does not independently recompute the
authors' differential-expression models from the full cell-level data. It does not replace expert
review or wet-lab follow-up.

## Dataset and feasible analysis route

The official dataset contains approximately 22 million primary human CD4+ T cells from four donors
under three culture conditions:

- `Rest` - resting/unstimulated;
- `Stim8hr` - stimulation for 8 hours;
- `Stim48hr` - stimulation for 48 hours.

The 12 donor-condition cell-level `.h5ad` files total 1,735,835,115,866 bytes, approximately
1.58 TiB. The project therefore uses the public summary-table route:

1. `DE_stats.suppl_table.csv` - 33,983 perturbation-condition rows;
2. `sample_metadata.suppl_table.csv` - 12 donor-condition sample rows;
3. `polarization_prediction_condition_comparison_regulator_coefficients.csv` - authors'
   activation/polarization model coefficients for descriptive annotation;
4. `IL10_IL21_arrayed_validation.csv` - 53 rows from the authors' small arrayed follow-up.

This is an intentional scientific and engineering boundary. It makes the analysis reproducible on
a normal computer while limiting the claim to auditing and prioritizing source-reported results.
For sources, schemas, sizes, and direct links, read
[`docs/OFFICIAL_DATASET.md`](./docs/OFFICIAL_DATASET.md).

## Scientific question

> Within each culture condition, which gene perturbations have broad downstream transcriptional
> consequences and remain credible after requiring effective negative on-target knockdown,
> sufficient targeted cells, no author-flagged off-target signal, and positive source-reported
> cross-donor and cross-guide concordance?

The answer consists of:

1. an auditable gate-by-gate screen funnel;
2. a ranked table for every eligible perturbation-condition row;
3. a concise shortlist per condition;
4. a descriptive weakest-condition ranking among genes that pass every gate in all three
   conditions;
5. descriptive source polarization annotations for eligible genes;
6. a descriptive donor-matched summary of the authors' arrayed IL-10/IL-21 follow-up.

An honest empty shortlist is allowed. The pipeline must not relax a gate merely to produce a
headline.

## Pre-registered triage contract

### Eligibility gates

Apply these rules to each perturbation-condition row in order and retain the reason for every
exclusion:

| Gate | Exact rule | Why it is required | What it does not prove |
|---|---|---|---|
| On-target significance | `ontarget_significant == True` | The source analysis detected target knockdown at its stated 10% FDR rule. | That knockdown is complete, functional, or independently reproduced. |
| Correct direction | `ontarget_effect_size < 0` | CRISPRi should reduce target expression. | That the size is sufficient for a phenotype. |
| Off-target flag | `offtarget_flag == False` | Excludes rows the source table flags for a potential off-target issue. | Absence of all off-target biology. |
| Coverage | `n_cells_target >= 100` | Removes very sparse perturbation-condition estimates. | Equal power across retained rows. |
| Donor concordance | `crossdonor_correlation_min` is present and `> 0` | Requires measured, directionally positive agreement across the source donor-pair analyses. | An independent recomputation by this project. |
| Guide concordance | `crossguide_correlation` is present and `> 0` | Requires measured, directionally positive agreement between source guide-level estimates. | That every guide is specific or equally effective. |

`False`, missing, zero, and negative values must not be silently converted into passes. Gate counts
must reconcile from the input through the final eligible set.

### Ranking rule

Ranking happens separately within `Rest`, `Stim8hr`, and `Stim48hr`. For eligible rows, compute the
within-condition percentile rank of these three metrics, where higher is better:

- `n_downstream`;
- source `crossdonor_correlation_min`, written as `crossdonor_min` in result tables;
- source `crossguide_correlation`, written as `crossguide` in result tables.

Then calculate:

```text
priority_score = (n_downstream_percentile
                  * crossdonor_min_percentile
                  * crossguide_percentile) ** (1/3)
```

Sort by descending `priority_score`, retaining the component metrics and ranks. The geometric mean
penalizes imbalance: a candidate cannot fully compensate for weak donor concordance with a very
large downstream-discovery count.

### Correct interpretation of the components

`n_downstream` is the authors' number of downstream genes called significant at **10% FDR** after
excluding the on-target effect. It is a discovery count, not an effect size. It depends on cell
count, expression, dispersion, and statistical power; a larger value does not by itself mean a
larger or more useful biological effect.

`crossdonor_correlation_min` and `crossguide_correlation` are author-reported reproducibility
summaries. This project checks that they exist, gates on positive values, and uses their relative
ranks. It does not independently reproduce those correlations from the large donor-pair and
guide-level matrices.

The `priority_score` is a transparent heuristic on a 0-1 relative scale. It is not a calibrated
probability of success, an FDR, or a therapeutic score.

## Arrayed IL-10/IL-21 follow-up

The authors provide a small file called `IL10_IL21_arrayed_validation.csv`. It contains reported
IL-10 and IL-21 percentages for nine selected perturbations and non-targeting controls across six
follow-up donors, with incomplete perturbation coverage across donors.

For each donor and cytokine, the workflow computes the mean of controls whose perturbation label
starts with `NTC`. Each perturbation value is shown as a donor-matched difference from that control
mean. It then summarizes available donor deltas without imputing missing perturbations.

This section is **descriptive only**:

- no confirmatory p-value is produced;
- no claim of screen-wide validation is made;
- missing or uneven donor coverage is shown, not hidden;
- the reported percentages do not independently establish the broad transcriptional mechanism;
- the word `validation` in the source filename is not adopted as this project's claim.

The safe phrase is: "the candidate has an author-provided arrayed follow-up measurement with the
following donor-matched descriptive pattern."

## Source polarization annotation

For genes that pass the source-QC gates, the workflow selects matching rows from the authors'
`polarization_prediction_condition_comparison_regulator_coefficients.csv`. It retains the source
coefficient fields and marks whether each regulator appears in the per-condition shortlist or the
cross-condition candidate set.

These coefficients come from the authors' prediction models for activation and polarization
signatures. They provide descriptive biological context only. This project does not refit the
models, test a new polarization hypothesis, or treat coefficient overlap as independent
validation.

## Cross-condition analysis

Candidate ranks are computed within condition. The cross-condition output retains only genes that
pass every gate in all three conditions. For each gene it reports the three condition-specific
scores, their minimum and mean, and the condition with the minimum score. It ranks genes by the
minimum score so the weakest condition controls the cross-condition order.

These differences are **descriptive**. The workflow does not fit a perturbation-by-condition
interaction model and therefore cannot claim that a perturbation acts significantly more strongly
in one condition. The sample metadata also needs to remain visible when discussing run/batch
structure.

## Required outputs

The official run must create an auditable bundle under `output/official/` containing:

- `provenance/source_audit.json` and `tables/sample_design_summary.csv` - source hashes, schemas,
  row counts, missingness, donors, conditions, and blockers;
- `tables/source_qc_decisions.csv` - per-source-row gate decisions and exclusion reasons;
- `tables/filter_funnel.csv` and `figures/01_filter_funnel.png` - starting rows and remaining rows
  after each registered gate;
- `tables/candidate_scores.csv` - all eligible rows, component ranks, `priority_score`, and final
  rank;
- `tables/top_candidates_by_condition.csv` and `figures/02_top_candidates.png` - a
  presentation-sized shortlist without discarding the full table;
- `tables/cross_condition_candidates.csv` and `figures/03_cross_condition_scores.png` - genes
  passing source QC in all three conditions, ranked by their minimum condition-specific score;
- `tables/candidate_polarization_coefficients.csv` - source coefficient annotations for
  source-QC-pass genes, including shortlist/cross-condition membership flags;
- `tables/validation_donor_deltas.csv`, `tables/validation_summary.csv`, and
  `figures/04_arrayed_validation_deltas.png` - donor-matched descriptive follow-up;
- `report.md`, `methods.md`, `run_summary.json`, and `provenance/manifest.json` - plain-language
  results, methods, machine-readable summary, and output provenance.

## Claim ladder

Use the strongest phrase whose evidence is actually present:

1. **Source row:** present in the authors' summary table.
2. **Eligible row:** passes every registered source-QC gate.
3. **Prioritized candidate:** ranks highly by the registered geometric-mean score within a
   condition.
4. **Reproducible candidate:** passes every source-QC gate in Rest, Stim8hr, and Stim48hr, then is
   ranked across conditions by its minimum condition-specific score.
5. **Independently validated:** requires a new, adequately powered orthogonal experiment and is
   outside this project.

Do not use "verified" or "validated" for levels 1-4.

## Principal limitations

- The main workflow consumes source summaries rather than raw counts.
- Source DE calls use a 10% FDR threshold; this project does not refit or alter that model.
- Four screen donors limit population generalization.
- Positive source correlations can still be small and uncertain.
- `offtarget_flag == False` means "not flagged by this source field," not "off-target-free."
- `n_cells_target >= 100` improves minimum coverage but does not equalize power.
- Percentile ranks are cohort-relative and can change when the candidate universe changes.
- Cross-condition plots are not formal interaction tests.
- Polarization coefficients are source-reported descriptive annotations, not an independent test.
- The small IL-10/IL-21 follow-up is selected, incomplete, and descriptive.
- No result here demonstrates clinical efficacy, safety, druggability, or causal therapeutic
  benefit.

## Reusable engineering pattern

The transferable lesson is not a particular gene. It is the architecture:

> Preserve the source result, expose every eligibility gate, rank only among comparable rows,
> keep the score decomposable, and make the claim no stronger than the recomputation actually
> performed.

This pattern transfers to evidence triage in legal, finance, cyber, and other scientific domains.

## Legacy teaching project

The deterministic CD8+ exhaustion workflow remains in the repository to teach single-cell
normalization, UMAP, annotation, donor-level pseudobulk, and pseudoreplication. Its dataset is
simulated and watermarked. It is not the recommended hackathon dataset and must not appear in the
official-data claim.

Run it only as a learning fallback:

```powershell
uv run tcell-triage demo --evidence evidence/literature_evidence.csv
uv run jupyter lab notebooks/01_cd8_exhaustion_triage_tutorial.ipynb
```
