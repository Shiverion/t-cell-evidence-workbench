# Learn the official outputs

Read this before memorizing code. The official workflow produces a transparent prioritization of
source-reported CD4+ Perturb-seq results. It does not independently reanalyze 22 million cells.

## The result in one sentence

With the pinned sources and default contract, **497 Rest**, **593 Stim8hr**, and **562 Stim48hr**
rows pass all six gates. A total of **224 genes** pass in all three conditions; **SETDB1** has the
highest minimum condition score, approximately **0.915**, with Stim8hr as its weakest condition.

The appropriate within-condition label is **source-QC candidate**. The workflow reserves
**reproducible candidate** for genes passing every gate in all three conditions. Do not call either
result verified or validated.

## 1. Dataset audit

Artifacts: `provenance/source_audit.json` and `tables/sample_design_summary.csv`

What it shows:

- which public files were used;
- whether required columns are present;
- source row counts and missingness;
- observed culture conditions;
- donor and sample counts from metadata;
- whether the run can proceed or has a blocker.

What to check:

- 33,983 DE summary rows before filtering;
- exactly `Rest`, `Stim8hr`, and `Stim48hr`;
- four unique donors and 12 donor-condition metadata rows;
- numeric and Boolean fields parsed correctly;
- missing donor/guide correlations counted explicitly.

What it does not show: whether the authors' biological or statistical model is correct. A schema
audit verifies that this workflow received the expected kind of input, not that every source value
is true.

## 2. Screen funnel

Artifacts: `tables/source_qc_decisions.csv`, `tables/filter_funnel.csv`, and
`figures/01_filter_funnel.png`

Each stage removes rows that fail one registered rule:

1. significant on-target knockdown (`ontarget_significant == True`);
2. correct CRISPRi direction (`ontarget_effect_size < 0`);
3. no source off-target flag (`offtarget_flag == False`);
4. at least 100 targeted cells (`n_cells_target >= 100`);
5. measured positive minimum donor correlation;
6. measured positive guide correlation.

How to read it: the height or count at each step is the number of perturbation-condition rows still
eligible. Counts should only stay the same or decrease.

What to check:

- the last funnel count equals the row count of `tables/candidate_scores.csv`;
- missing, zero, or negative correlations do not pass;
- positive on-target effects do not pass even if the source significance flag is true;
- the order and thresholds match `configs/official_cd4.yaml`.

What not to say: "rows removed by the funnel have no biological effect." Exclusion means the row
lacks the evidence required by this triage contract. It may be underpowered, untested for a metric,
inconsistent, or flagged for a quality concern.

For the pinned default run, the final funnel counts are 497 Rest, 593 Stim8hr, and 562 Stim48hr.
The large drop at the donor-correlation gate mainly says that measured positive donor concordance
is a demanding eligibility requirement; it does not prove every removed perturbation is false.

## 3. Full triaged table

Artifact: `tables/candidate_scores.csv`

This is the primary auditable result. It retains every eligible perturbation-condition row and the
components needed to reproduce its rank.

The three source ranking metrics, with their result-table names, are:

- `n_downstream` - number of source DE discoveries at 10% FDR, excluding on-target effect;
- `crossdonor_min` - renamed source `crossdonor_correlation_min`, the worst reported donor-pair
  concordance summary;
- `crossguide` - renamed source `crossguide_correlation`, the reported guide concordance.

Each metric is converted to a percentile rank **within its culture condition**. The score is:

```text
priority_score = (n_downstream_percentile
                  * crossdonor_min_percentile
                  * crossguide_percentile) ** (1/3)
```

Higher scores mean a row ranks well across the three chosen source metrics relative to other
eligible rows in the same condition.

What to check for any candidate:

- all original gate fields are retained;
- all three component values and ranks are visible;
- the score agrees with the cube root of their product;
- the final rank resets within each condition;
- ties and missingness are represented consistently.

What the score is not:

- not a p-value or FDR;
- not the probability that an experiment will succeed;
- not a direct perturbation effect size;
- not a druggability, safety, or clinical score;
- not comparable across conditions as if each condition had the same candidate universe.

### Why `n_downstream` needs special care

`n_downstream` counts genes that passed the authors' 10% FDR rule. More cells and greater power can
increase this count. Gene expression, variance, and model eligibility also matter. Say "more
source-reported downstream discoveries," not "a larger biological effect."

### Why the correlations need special care

The authors computed the donor and guide correlations from larger stratified analyses. This
summary pipeline did not independently recompute them. Say "positive author-reported
concordance," not "independently replicated by our pipeline."

## 4. Top candidates by condition

Artifacts: `tables/top_candidates_by_condition.csv` and `figures/02_top_candidates.png`

This is a presentation-sized view of the highest-ranked eligible rows for `Rest`, `Stim8hr`, and
`Stim48hr`. It should display enough component information to explain why each candidate ranked
highly.

Use it to answer: "Which small set should an expert inspect first within this condition?"

Do not hide the full triaged table. A shortlist without the complete eligible universe makes the
selection difficult to audit.

When presenting one row, identify its weakest component as well as its strongest. The geometric
mean is designed to reward balance, so the explanation should reflect all three metrics.

The default condition leaders are:

| Condition | Gene | Priority score |
|---|---|---:|
| Rest | SETDB1 | 0.945 |
| Stim8hr | ARNT | 0.916 |
| Stim48hr | ARNT | 0.942 |

## 5. Cross-condition candidates

Artifacts: `tables/cross_condition_candidates.csv` and `figures/03_cross_condition_scores.png`

The table contains only genes with a source-QC pass in all three conditions. It shows each
condition's `priority_score`, their minimum and mean, the `worst_condition`, and a
`cross_condition_rank` based on the minimum score. The heatmap visualizes those complete
three-condition score profiles.

What they do not show: a formal perturbation-by-condition interaction. A rank change can reflect a
different eligible comparison set, cell count, power, missing metrics, or a true biological change.
This workflow does not separate those explanations statistically.

Safe sentence: "Target X passed source QC in all three conditions; Stim48hr was its weakest
condition-specific priority score."

Unsafe sentence: "Target X has a significantly weaker biological effect at 48 hours."

In the pinned run, 224 genes enter this table. SETDB1 ranks first because its lowest score across
the three conditions is 0.915, slightly higher than every other gene's lowest score. That is a
maximin prioritization result, not evidence that SETDB1 has the largest biological effect.

## 6. Candidate polarization coefficients

Artifact: `tables/candidate_polarization_coefficients.csv`

This table selects authors' activation/polarization coefficient rows whose `regulator` is a gene
that passed the source-QC gates. It retains source fields such as the signature, condition,
coefficient, rank, and known-regulator annotation. It also reports whether the gene is in a
per-condition top list or the cross-condition candidate set.

Use it to ask: "What source-reported activation or polarization context is available for this
eligible candidate?"

Do not use it to say the project independently reproduced a polarization effect. The coefficients
were computed by the source authors; this workflow performs a transparent join and annotation.

## 7. Arrayed IL-10/IL-21 donor deltas

Artifacts: `tables/validation_donor_deltas.csv`, `tables/validation_summary.csv`, and
`figures/04_arrayed_validation_deltas.png`

The source file reports `IL10_perc` and `IL21_perc` for selected perturbations and non-targeting
controls in six follow-up donors. Coverage is uneven.

For each donor and cytokine, the workflow averages available control labels beginning with `NTC`.
It then computes:

```text
donor_delta = perturbation_percentage - donor_mean_NTC_percentage
```

How to read it:

- positive delta - above that donor's non-targeting-control mean;
- negative delta - below that donor's non-targeting-control mean;
- donor count - how many observed donor comparisons support the descriptive summary;
- spread across donors - whether the direction looks stable or heterogeneous.

Important limits:

- perturbations were selected for this small follow-up;
- not every perturbation is observed in every donor;
- the workflow does not impute missing values;
- it does not run a confirmatory model or multiplicity correction;
- cytokine percentages do not directly confirm the screen-wide downstream-gene mechanism;
- this is author-provided follow-up, not an independent experiment run by this project.

For orientation, the default summary reports a mean IL-10 delta of about +12.755 percentage points
for ELOB across three available donors and a mean IL-21 delta of about +5.262 points for ATP2A2
across five. Those are descriptive averages from selected, uneven follow-up data, not confirmatory
estimates.

The source filename uses `validation`; the output should still be described as **descriptive
arrayed follow-up**.

## 8. Provenance and report

Artifacts: `report.md`, `methods.md`, `run_summary.json`, and `provenance/manifest.json`

The provenance should let another person answer:

- which URLs and local files were used;
- when they were downloaded;
- what configuration and thresholds were applied;
- what software versions ran;
- which output belongs to this exact run.

The report should restate the question, gate counts, ranking method, shortlists, and limitations in
plain language. It must keep the difference between source-reported statistics and project-computed
transformations visible.

## The one explanation to remember

> This workflow does not ask which row has the most impressive single number. It first requires a
> complete minimum evidence package, then ranks eligible rows by a balance of downstream discovery,
> donor concordance, and guide concordance within condition.

## Language guide

| Prefer | Avoid | Why |
|---|---|---|
| source-QC candidate | verified hit | The source correlations were not independently recomputed here. |
| reproducible candidate passing source QC in all three conditions | validated target | Experimental validation is outside this workflow. |
| more downstream discoveries | larger effect | `n_downstream` is a power-dependent FDR discovery count. |
| ranked higher within Stim8hr | works better at 8 hours | No condition interaction test was fitted. |
| has a source polarization annotation | independently reproduced polarization | The coefficient comes from the authors' model. |
| not flagged by the source field | off-target-free | A flag cannot exclude every off-target mechanism. |
| descriptive donor-matched follow-up | confirmed cytokine mechanism | The small arrayed table is selected and incomplete. |

## Eight-question self-check

1. Why is a significant positive on-target effect inconsistent with the CRISPRi gate?
2. Why do missing correlations fail the source-QC contract?
3. Why is a 100-cell minimum not equal power across rows?
4. What does 10% FDR mean for `n_downstream`?
5. Why use within-condition percentile ranks?
6. What behavior does the geometric mean reward?
7. Why is a cross-condition heatmap not an interaction test?
8. What additional evidence would justify the word "validated"?

If you can answer those from memory and manually verify one score, move to the official tutorial
notebook and teach the workflow back aloud.

## Legacy output note

Files under `output/demo/` and the notebook
`notebooks/01_cd8_exhaustion_triage_tutorial.ipynb` belong to the simulated CD8+ teaching fallback.
They demonstrate different methods and contain an injected answer. They are not outputs from the
official CD4+ Perturb-seq dataset.
