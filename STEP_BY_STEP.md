# Step by Step: Official CD4+ Perturb-seq Triage

This is the first-timer runbook for the official
[Primary Human CD4+ T Cell Perturb-seq dataset](https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq)
recommended by the
[Built with Claude: Life Sciences](https://cerebralvalley.ai/e/built-with-claude-life-sciences)
research track.

The workflow is intentionally lightweight. It analyzes the authors' public summary statistics
instead of downloading approximately 1.58 TiB of cell-level files. Your job is to understand and
defend every filter, ranking component, and limitation.

## The learning loop

Use this loop for every table and figure:

1. Read its plain-language description.
2. Hide the description and explain the artifact aloud in your own words.
3. Name the input columns and transformation that created it.
4. State one conclusion it supports.
5. State one tempting conclusion it does **not** support.
6. Check one row or point manually against the preceding artifact.

Do not move on merely because the output looks polished.

## Stage 0 - Understand the experiment

### 0.1 Read the official sources

Open these before running code:

- [Virtual Cells Platform dataset card](https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq)
- [Authors' data-sharing README](https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/data_sharing_readme.md)
- [Authors' supplementary tables](https://github.com/emdann/GWT_perturbseq_analysis_2025/tree/master/metadata/suppl_tables)
- [This repository's dataset guide](./docs/OFFICIAL_DATASET.md)

Write these facts from memory:

- cell type: primary human CD4+ T cells;
- perturbation: genome-scale CRISPR interference, abbreviated CRISPRi;
- scale: approximately 22 million cells;
- biological replicates: four donors;
- conditions: Rest, Stim8hr, and Stim48hr;
- main source table: 33,983 perturbation-condition rows.

### 0.2 Learn the five essential terms

- **Perturbation:** experimental reduction of a target gene using one or more guide RNAs.
- **On-target knockdown:** evidence that the intended target gene decreased.
- **Downstream gene:** another gene whose expression changed after the perturbation.
- **Cross-donor concordance:** similarity of the estimated perturbation response across donor
  subsets.
- **Cross-guide concordance:** similarity of the response estimated using different guides for the
  same target.

The last two statistics are supplied by the authors. The summary workflow does not recompute them
from the full matrices.

### 0.3 Lock the question and claim boundary

Copy this question into your notes:

> Which perturbations produce broad downstream transcriptional effects and pass the registered
> source-QC checks within each culture condition?

Copy this claim boundary too:

> A high-ranked condition row is a source-QC candidate. "Reproducible candidate" is reserved for a
> gene that passes every gate in all three conditions. Neither label means independently verified
> or experimentally validated.

## Stage 1 - Install and run

### 1.1 Prepare the environment

From the repository root in Windows PowerShell:

```powershell
uv sync --extra dev
```

This installs the pinned environment from `uv.lock`.

### 1.2 Run the complete official workflow

```powershell
uv run perturbseq-triage all --data-dir data/official --output-dir output/official
```

The command should:

1. download the public summary tables;
2. verify their required columns and study design;
3. apply the six registered gates;
4. calculate within-condition percentile ranks and the geometric-mean score;
5. write full and presentation-sized candidate tables;
6. join source-reported activation/polarization coefficients as descriptive annotation;
7. rank genes passing all three conditions by their weakest condition score;
8. calculate donor-matched IL-10/IL-21 follow-up deltas descriptively;
9. write figures, report text, and provenance.

It should not download any `D*_*.assigned_guide.h5ad` file.

### 1.3 Open the official notebook

```powershell
uv run jupyter lab notebooks/02_cd4_perturbseq_official_tutorial.ipynb
```

Use the notebook to learn the finished outputs. Use the CLI for the clean reproducible run. Both
should point at the same official summary inputs and implement the same contract.

## Stage 2 - Audit the inputs

Open `output/official/provenance/source_audit.json` and
`output/official/tables/sample_design_summary.csv` first. Confirm:

- the DE table has 33,983 rows before filtering;
- conditions are exactly `Rest`, `Stim8hr`, and `Stim48hr`;
- sample metadata represents four unique donors and 12 donor-condition rows;
- all required columns are present;
- numeric columns parse as numeric rather than strings;
- Boolean fields have not silently acquired unexpected categories;
- missing donor and guide correlations are counted;
- the local inputs can be traced to exact public URLs.

Required DE columns are:

```text
target_contrast_gene_name
culture_condition
n_cells_target
ontarget_effect_size
ontarget_significant
offtarget_flag
n_downstream
crossdonor_correlation_min
crossguide_correlation
```

Stop if the schema or conditions differ. Do not rename an unfamiliar column by guesswork.

### Manual check

Pick any three source rows. For each, say whether it should pass the on-target direction and cell
count gates before looking at the pipeline's result. Then compare your prediction with the audit.

## Stage 3 - Understand the screen funnel

Open `output/official/tables/source_qc_decisions.csv`,
`output/official/tables/filter_funnel.csv`, and
`output/official/figures/01_filter_funnel.png`. The registered gates are:

1. `ontarget_significant == True`;
2. `ontarget_effect_size < 0`;
3. `offtarget_flag == False`;
4. `n_cells_target >= 100`;
5. `crossdonor_correlation_min` is present and greater than zero;
6. `crossguide_correlation` is present and greater than zero.

Each gate answers a different question. Passing one cannot substitute for failing another.

### What to verify

- counts never increase as the funnel progresses;
- the final count equals the number of rows in `tables/candidate_scores.csv`;
- missing correlations fail their respective gates;
- zero correlations do not pass a strict `> 0` rule;
- a positive on-target effect does not pass CRISPRi direction even if marked significant;
- a flagged potential off-target row is excluded.

### What not to say

Do not say "the excluded genes are biologically unimportant." A row can fail because the source
screen lacked power, a metric was not measured, guide behavior was inconsistent, or the project
set a conservative minimum. The funnel defines eligibility for this triage, not biological truth.

## Stage 4 - Understand the ranking

Open `output/official/tables/candidate_scores.csv`. Eligible rows are ranked separately within
each culture condition.

For each row, inspect:

- `n_downstream` and `n_downstream_percentile`;
- source donor metric `crossdonor_min` and `crossdonor_min_percentile`;
- source guide metric `crossguide` and `crossguide_percentile`;
- the geometric-mean `priority_score`;
- the final within-condition rank.

The score is:

```text
priority_score = (n_downstream_percentile
                  * crossdonor_min_percentile
                  * crossguide_percentile) ** (1/3)
```

### Why use a geometric mean?

It makes balance matter. A candidate that is excellent on downstream discovery count but weak on
donor agreement should not look identical to one that is consistently strong across all three
dimensions.

### The most important warning

`n_downstream` is the number of downstream genes called significant by the authors at 10% FDR,
excluding the on-target effect. It is affected by cell count and statistical power. It is **not**
an effect-size measure, and twice as many discoveries does not mean twice the biological effect.

The score is also not a probability. A score of 0.90 does not mean a 90% chance of experimental
success.

### Manual check

Choose one candidate from the top five in each condition. Recalculate the product of its three
percentile ranks and take the cube root with a calculator. Confirm the reported score to rounding.
Then identify its weakest component.

## Stage 5 - Build a defensible shortlist

Open `output/official/tables/top_candidates_by_condition.csv` and
`output/official/figures/02_top_candidates.png`.

For each shortlisted row, be able to answer:

1. Which condition was it ranked in?
2. Did it pass all six gates?
3. How many downstream discoveries did the source report?
4. What were the minimum donor and guide correlations?
5. Which component most limits its score?
6. What independent experiment would you run next?

The shortlist is for presentation. The full `tables/candidate_scores.csv` remains the auditable
ranked record, while `tables/source_qc_decisions.csv` preserves every source-row decision. Both
must ship with it.

## Stage 6 - Read the cross-condition view correctly

Open `output/official/tables/cross_condition_candidates.csv` and
`output/official/figures/03_cross_condition_scores.png`.

The table contains only genes that pass every gate in all three conditions. It shows each
condition-specific score, the minimum and mean score, the `worst_condition`, and a
`cross_condition_rank` determined by the minimum score. This rewards a strong weakest condition.

It cannot establish a condition-specific causal effect. The pipeline does not fit a formal
perturbation-by-condition interaction model. A candidate ranking higher in Stim48hr than Stim8hr
may reflect the eligible comparison set, power, cell count, or the underlying source statistics.

Use: "passed source QC in all three conditions; its lowest priority score was in Stim48hr."

Do not use: "has a significantly stronger effect after 48 hours."

## Stage 7 - Read the polarization annotation correctly

Open `output/official/tables/candidate_polarization_coefficients.csv`. It contains rows from the authors'
activation/polarization coefficient table for regulators that also pass this project's source-QC
gates. Membership flags show whether the regulator appears in a per-condition top list or the
cross-condition candidate set.

Use this table to add source context, such as which signature and condition a coefficient belongs
to. Do not call the coefficient a new result from this project: the pipeline does not refit the
authors' model or run an independent polarization test.

## Stage 8 - Read the IL-10/IL-21 follow-up correctly

Open `output/official/tables/validation_donor_deltas.csv`,
`output/official/tables/validation_summary.csv`, and
`output/official/figures/04_arrayed_validation_deltas.png`.

The source file reports `IL10_perc` and `IL21_perc` for selected perturbations and non-targeting
controls. For each donor, the workflow:

1. identifies control labels beginning with `NTC`;
2. averages available NTC values for each cytokine;
3. subtracts that donor-matched control mean from each perturbation value;
4. summarizes only the observed donor deltas.

A positive delta means the reported percentage was above that donor's NTC mean; a negative delta
means it was below. Check the number of donors because perturbation coverage is uneven.

This is descriptive. Do not add a p-value after seeing the plot, treat missing donors as zeros, or
call it independent validation. The authors chose the perturbations in this small follow-up, and
the filename's word `validation` is not a license to strengthen this project's claim.

## Stage 9 - Write the result in your own words

Use this four-sentence template and replace every bracket:

> We audited 33,983 source-reported perturbation-condition results from a four-donor primary CD4+
> T-cell CRISPRi screen. After requiring [list the six gates], [N] rows were eligible across the
> three culture conditions. [Candidate] ranked highly in [condition] because it balanced
> downstream discovery count with positive author-reported donor and guide concordance. This is a
> source-QC candidate for independent follow-up, not an independently verified or validated
> target. If it passes all three conditions, say so before using "reproducible candidate."

If discussing the arrayed file, add a separate sentence that calls it an author-provided,
donor-matched **descriptive** follow-up.

## Stage 10 - Reproduce and package

Run the checks:

```powershell
uv run pytest -q
uv run ruff check src tests scripts
uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 notebooks/02_cd4_perturbseq_official_tutorial.ipynb
```

Then complete [`docs/SUBMISSION_CHECKLIST.md`](./docs/SUBMISSION_CHECKLIST.md). Re-run the official
command from a clean output directory or fresh clone before submission, while preserving the
downloaded inputs and provenance needed for reproducibility.

## Optional - Explore the full dataset later

The Virtual Cells Platform documents public CLI and S3 access. The discovery command is:

```powershell
vcp data search "Primary Human CD4+ T Cell Perturb-seq" --exact
```

Do not start the full download casually. The 12 cell-level files total approximately 1.58 TiB; the
pseudobulk and DE matrix artifacts are also tens of gigabytes. A full reanalysis needs adequate
storage, memory, transfer time, and a new statistical plan. It would be a separate extension, not
a hidden step in this workflow.

## Legacy synthetic learning fallback

If you want to learn UMAP, marker annotation, donor pseudobulk, and per-cell pseudoreplication on a
small deterministic fixture, use the earlier CD8+ tutorial:

```powershell
uv run tcell-triage demo --evidence evidence/literature_evidence.csv
uv run jupyter lab notebooks/01_cd8_exhaustion_triage_tutorial.ipynb
```

That dataset is simulated. Its injected result is a software test and teaching example, not part
of the official CD4+ Perturb-seq result.

## Final self-check

You are ready to present only if you can answer these without notes:

1. Why is the official question about CD4+ perturbations rather than CD8+ exhaustion?
2. Why does the project use summary tables instead of the cell matrices?
3. Why must significant CRISPRi on-target effects also be negative?
4. Why do missing donor or guide correlations fail eligibility?
5. Why is `n_downstream` not an effect size?
6. What does the geometric mean reward?
7. Why are condition differences descriptive rather than interaction claims?
8. Why is the IL-10/IL-21 section descriptive despite the source filename?
9. What evidence would be needed before saying "validated"?
