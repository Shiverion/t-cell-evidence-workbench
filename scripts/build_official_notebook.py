"""Build the teaching notebook for the official CD4 Perturb-seq project."""

from __future__ import annotations

from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "02_cd4_perturbseq_official_tutorial.ipynb"


def markdown(text: str) -> nbformat.NotebookNode:
    """Create a clean Markdown cell."""

    return nbformat.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str) -> nbformat.NotebookNode:
    """Create an unexecuted Python cell."""

    return nbformat.v4.new_code_cell(text.strip() + "\n")


def main() -> None:
    """Populate the tutorial scaffold and clear all execution state."""

    notebook = nbformat.read(NOTEBOOK, as_version=4)
    notebook.cells = [
        markdown(
            """
# Official CD4+ T-cell Perturb-seq Candidate Triage

> **What this is:** a teaching walkthrough of the official hackathon-recommended dataset.
> **What this is not:** an independent reanalysis of all 22 million single cells or wet-lab
> validation of a drug target.

**Audience:** learners who know basic Python/dataframes and want to understand how a large
Perturb-seq study can be turned into a cautious, auditable target-triage result.

**Prerequisites:**

- install the project with `uv sync --extra dev`;
- internet access on the first run so the CLI can retrieve the public source tables;
- basic familiarity with rows, columns, averages, and rankings;
- no prior CRISPR or single-cell analysis experience is required.

**Learning goals:** by the end, you can explain:

- what CRISPRi, guide RNAs, non-targeting controls, donors, and culture conditions mean;
- how the source-table audit and hard-filter funnel protect the analysis;
- what the composite score does and does **not** measure;
- why cross-condition rankings are descriptive, not interaction tests;
- how donor-matched IL10/IL21 follow-up strengthens or weakens a candidate story;
- which conclusions are recomputed here and which remain source-reported.
"""
        ),
        markdown(
            """
## Outline

1. Run the reproducible command-line workflow.
2. Learn the official dataset and experimental vocabulary.
3. Audit the downloaded source tables and study design.
4. Follow candidates through the hard-filter funnel.
5. Decompose the composite priority score.
6. Read the top candidates within each condition.
7. interpret the cross-condition ranking without inventing an interaction.
8. Inspect the authors' polarization-model annotations descriptively.
9. Inspect donor-matched IL10 and IL21 follow-up.
10. Practice the limitations, pitfalls, and next experiments.

Expected time: 45-75 minutes, including exercises.
"""
        ),
        markdown(
            """
## The question and the evidence boundary

The project asks a **triage** question:

> Which perturbations pass predeclared source-quality gates and rank highly on a transparent
> combination of source-reported discovery breadth and reproducibility?

The workflow starts from the authors' public processed tables. It recomputes the audit, filters,
percentile features, geometric-mean rankings, donor-matched cytokine deltas, figures, and report.
It does not
download and refit the full cell-level model.

Two boundaries matter throughout:

1. `crossdonor_min` and `crossguide` are **source-reported reproducibility summaries**, not an
   independent recomputation from raw cells in this project.
2. `n_downstream` is the authors' count of downstream discoveries at **10% FDR**. It is
   power-dependent: more cells, lower noise, and larger effects can produce more discoveries.
   It is not a direct meter of biological importance.
"""
        ),
        code(
            """
from __future__ import annotations

from pathlib import Path
import json
import subprocess

import pandas as pd
from IPython.display import Image, Markdown, display


def find_project_root(start: Path) -> Path:
    # Work whether Jupyter started in the repository or in notebooks/.
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError("Could not find pyproject.toml from the current directory")


PROJECT_ROOT = find_project_root(Path.cwd().resolve())
DATA_DIR = PROJECT_ROOT / "data" / "official"
OUTPUT_DIR = PROJECT_ROOT / "output" / "official"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"

print(f"Project root: {PROJECT_ROOT}")
print(f"Official data cache: {DATA_DIR}")
print(f"Analysis output: {OUTPUT_DIR}")
"""
        ),
        markdown(
            """
## Step 1 - Run the complete official-data workflow

The next cell runs the same CLI a reviewer can run from a terminal. `cwd=PROJECT_ROOT` makes the
relative input and output paths unambiguous. The command downloads/caches the manageable public
source tables, validates them, performs the triage, and writes tables, figures, prose, and
provenance.

The command is intentionally explicit:

```text
uv run perturbseq-triage all --data-dir data/official --output-dir output/official
```
"""
        ),
        code(
            """
command = [
    "uv",
    "run",
    "perturbseq-triage",
    "all",
    "--data-dir",
    "data/official",
    "--output-dir",
    "output/official",
]

completed = subprocess.run(
    command,
    cwd=PROJECT_ROOT,
    check=False,
    text=True,
    capture_output=True,
)
print(completed.stdout[-4_000:])
if completed.stderr:
    print("Diagnostic output:")
    print(completed.stderr[-2_000:])
completed.check_returncode()
"""
        ),
        markdown(
            """
### Confirm the analysis contract

A successful process exit is useful, but expected artifacts make the contract concrete. This
cell fails early if a partial run omitted a required table, figure, or provenance record.
"""
        ),
        code(
            """
expected_artifacts = [
    "provenance/source_audit.json",
    "provenance/manifest.json",
    "tables/source_qc_decisions.csv",
    "tables/filter_funnel.csv",
    "tables/candidate_scores.csv",
    "tables/top_candidates_by_condition.csv",
    "tables/cross_condition_candidates.csv",
    "tables/validation_donor_deltas.csv",
    "tables/validation_summary.csv",
    "tables/sample_design_summary.csv",
    "tables/candidate_polarization_coefficients.csv",
    "figures/01_filter_funnel.png",
    "figures/02_top_candidates.png",
    "figures/03_cross_condition_scores.png",
    "figures/04_arrayed_validation_deltas.png",
    "report.md",
    "methods.md",
]
artifact_check = pd.DataFrame(
    {
        "artifact": expected_artifacts,
        "exists": [(OUTPUT_DIR / name).is_file() for name in expected_artifacts],
    }
)
display(artifact_check)
assert artifact_check["exists"].all(), "The official run is incomplete; inspect the CLI output."
"""
        ),
        markdown(
            """
## Step 2 - Understand the official experiment

The recommended dataset is the
[Primary Human CD4+ T Cell Perturb-seq dataset][official-dataset].
It contains roughly 22 million cells from four donors under three culture conditions: `Rest`,
`Stim8hr`, and `Stim48hr`. The study used genome-scale CRISPR interference in primary human CD4+
T cells. This is the T-cell dataset linked by the
[Built with Claude: Life Sciences event][hackathon-event].

| Term | Plain-language meaning | Why it matters here |
|---|---|---|
| CRISPRi | A guide brings a repression system to a gene to reduce its expression. | It creates a directional intervention, but knockdown can be incomplete. |
| Guide RNA | The sequence that points CRISPRi toward a target gene. | Multiple guides can check whether an effect repeats for the same target. |
| NTC | A non-targeting control guide with no intended human-gene target. | It estimates the background state for comparison. |
| Donor | One person who supplied primary cells. | Donors are biological replicates; cells from one donor are not new people. |
| Condition | Resting, 8-hour stimulation, or 48-hour stimulation context. | A perturbation can behave differently as the cell state changes. |
| On-target effect | Evidence that the intended target was actually knocked down. | A weak intervention makes downstream interpretation less credible. |
| Downstream discovery | Another gene reported as responding to the perturbation. | Breadth can be useful, but is strongly affected by statistical power. |

The project deliberately uses the study's compact supplementary outputs rather than requiring a
learner to download the full cell-level collection. See the authors'
[data-sharing README][sharing-readme]
for the full file inventory.

[official-dataset]: https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq
[sharing-readme]: https://github.com/emdann/GWT_perturbseq_analysis_2025/blob/master/metadata/data_sharing_readme.md
[hackathon-event]: https://cerebralvalley.ai/e/built-with-claude-life-sciences
"""
        ),
        markdown(
            """
## Step 3 - Audit the source before scoring anything

An audit should answer: Which files were used? Did the checksums match? Are required columns and
conditions present? How many records were read? A ranking is not reproducible if its inputs are
ambiguous.
"""
        ),
        code(
            """
source_audit = json.loads(
    (OUTPUT_DIR / "provenance" / "source_audit.json").read_text(encoding="utf-8")
)
audit_view = pd.json_normalize(source_audit, sep=".").T
audit_view.columns = ["recorded value"]
display(audit_view)
"""
        ),
        markdown(
            """
### Inspect the experimental design represented in the source tables

The design summary prevents a common category error: a large number of rows or cells does not
imply a large number of independent donors. Read it before interpreting a score.
"""
        ),
        code(
            """
design = pd.read_csv(TABLE_DIR / "sample_design_summary.csv")
display(design)
"""
        ),
        markdown(
            """
### Inspect each source row and its gate decisions

`source_qc_decisions.csv` is the human-auditable ledger. It retains failed rows, the boolean
decision for every hard gate, the final `source_qc_pass`, and a readable failure reason. That is
safer than silently deleting records before anyone can inspect them.

The predeclared gates are:

| Gate | Passing rule |
|---|---|
| On-target significance | `ontarget_significant == True` |
| On-target direction | `ontarget_effect_size < 0` (the target was reduced) |
| Off-target flag | `offtarget_flag == False` |
| Target-cell support | `n_cells_target >= 100` |
| Cross-donor summary | `crossdonor_min` is present and greater than 0 |
| Cross-guide summary | `crossguide` is present and greater than 0 |
"""
        ),
        code(
            """
source_qc = pd.read_csv(TABLE_DIR / "source_qc_decisions.csv")
gate_columns = [
    column
    for column in source_qc.columns
    if (
        (column.endswith("_pass") or column.startswith("gate_"))
        and column != "source_qc_pass"
    )
]
summary_columns = [
    "gene",
    "culture_condition",
    "n_cells_target",
    "n_downstream",
    "ontarget_effect_size",
    "ontarget_significant",
    "offtarget_flag",
    "crossdonor_min",
    "crossguide",
    *gate_columns,
    "source_qc_pass",
    "qc_failure_reasons",
]
display(source_qc[summary_columns].head(12))
display(source_qc["source_qc_pass"].value_counts(dropna=False).rename("rows").to_frame())
"""
        ),
        markdown(
            """
## Step 4 - Follow the hard-filter funnel

Hard gates answer **eligibility**, not priority. They remove rows that do not meet the declared
minimum evidence requirements before any geometric-mean score is calculated. The funnel makes the
cost of each gate visible by condition; a sudden condition-specific collapse should trigger an
audit, not a celebratory top-hit list.
"""
        ),
        code(
            """
funnel = pd.read_csv(TABLE_DIR / "filter_funnel.csv")
funnel = funnel.sort_values(["culture_condition", "stage_order"])
display(
    funnel.pivot(
        index=["stage_order", "stage"],
        columns="culture_condition",
        values="n_rows",
    )
)
"""
        ),
        code(
            """
display(Image(filename=FIGURE_DIR / "01_filter_funnel.png", width=1000))
"""
        ),
        markdown(
            """
### Exercise 1 - Find the most restrictive gate

For each condition, calculate the number and fraction of rows lost at every step. Which step is
most restrictive? Then inspect a few rows with that failure reason before deciding whether the
threshold is scientifically sensible.
"""
        ),
        code(
            """
# Answer scaffold: keep the first stage as the denominator for an intuitive loss fraction.
exercise_1 = funnel.copy()
exercise_1["rows_lost_at_stage"] = -exercise_1.groupby("culture_condition")["n_rows"].diff()
exercise_1["starting_rows"] = exercise_1.groupby("culture_condition")["n_rows"].transform("first")
exercise_1["fraction_of_start_lost"] = (
    exercise_1["rows_lost_at_stage"] / exercise_1["starting_rows"]
)
exercise_1.sort_values(
    ["culture_condition", "rows_lost_at_stage"], ascending=[True, False]
).head(9)
"""
        ),
        markdown(
            """
## Step 5 - Read the composite priority score

Only rows that pass every hard gate receive a priority score. The workflow first converts each
component to a within-condition percentile so measurements with different units can be combined.
Higher percentiles always mean stronger evidence. Within each condition, pandas average ranks are
converted to percentiles with `rank(method="average", pct=True)`. The priority score is the
geometric mean of three ranks: `n_downstream_percentile`, `crossdonor_min_percentile`, and
`crossguide_percentile`.
A geometric mean rewards candidates that are jointly strong and penalizes a weak component. It
is a transparent ranking heuristic, not a probability of success and not a p-value.

Keep the evidence boundary visible:

- `crossdonor_min` and `crossguide` are the authors' reported reproducibility summaries. This
  workflow uses them; it does not independently refit them from the 22 million cells.
- `n_downstream` counts the authors' discoveries at 10% FDR. Because discovery counts depend on
  power, it should never dominate the score or be described as pure biological breadth.
- Ties and percentile choices can still affect ranks. The component columns remain available so
  a reviewer can audit the score directly.
"""
        ),
        code(
            """
scores = pd.read_csv(TABLE_DIR / "candidate_scores.csv")
percentile_columns = [
    "n_downstream_percentile",
    "crossdonor_min_percentile",
    "crossguide_percentile",
]
assert set(percentile_columns).issubset(scores.columns)
score_view = [
    "gene",
    "culture_condition",
    *percentile_columns,
    "priority_score",
    "candidate_label",
]
display(scores[score_view].sort_values("priority_score", ascending=False).head(15))
"""
        ),
        markdown(
            """
### Exercise 2 - Audit one candidate's score

Choose one row, identify its strongest and weakest percentile components, and recompute the
geometric mean. Explain why one very low component pulls down the score even when another
component is near the top of its condition.
"""
        ),
        code(
            """
# Answer scaffold: replace the first row with a candidate you want to audit.
candidate = scores.sort_values("priority_score", ascending=False).iloc[0]
components = candidate[percentile_columns].astype(float).sort_values(ascending=False)
recomputed_score = float(components.product() ** (1 / len(components)))
exercise_2 = {
    "gene": candidate["gene"],
    "condition": candidate["culture_condition"],
    "strongest_component": components.index[0],
    "weakest_component": components.index[-1],
    "reported_priority_score": float(candidate["priority_score"]),
    "recomputed_geometric_mean": recomputed_score,
    "why_the_weakest_component_matters": "TODO: explain in your own words",
}
exercise_2
"""
        ),
        markdown(
            """
## Step 6 - Read top candidates within each condition

Within-condition ranks are the primary output because resting, early-stimulated, and late-
stimulated cells are different biological contexts. Look across the component columns before
repeating the overall score: two candidates can tie for very different reasons.
"""
        ),
        code(
            """
top = pd.read_csv(TABLE_DIR / "top_candidates_by_condition.csv")
top_columns = [
    "culture_condition",
    "rank_within_condition",
    "gene",
    "priority_score",
    "candidate_label",
    *[column for column in percentile_columns if column in top.columns],
]
display(top[top_columns].sort_values(["culture_condition", "rank_within_condition"]))
"""
        ),
        code(
            """
display(Image(filename=FIGURE_DIR / "02_top_candidates.png", width=1050))
"""
        ),
        markdown(
            """
## Step 7 - Interpret the cross-condition table descriptively

The cross-condition table includes only genes that passed in all three conditions. It ranks them
by `min_priority_score`, the weakest of their three **separately calculated** scores.
`mean_priority_score` is a secondary descriptive summary. This is useful for triage, but it is
not a model of a gene-by-condition interaction and does not quantify uncertainty in score
differences.
"""
        ),
        code(
            """
cross_condition = pd.read_csv(TABLE_DIR / "cross_condition_candidates.csv")
condition_score_columns = [
    "Rest_priority_score",
    "Stim8hr_priority_score",
    "Stim48hr_priority_score",
]
cross_columns = [
    "cross_condition_rank",
    "gene",
    *condition_score_columns,
    "min_priority_score",
    "mean_priority_score",
    "worst_condition",
    "candidate_label",
]
display(cross_condition[cross_columns].sort_values("cross_condition_rank").head(15))
"""
        ),
        code(
            """
display(Image(filename=FIGURE_DIR / "03_cross_condition_scores.png", width=1000))
"""
        ),
        markdown(
            """
### Exercise 3 - Significant here, not significant there

Suppose a perturbation is significant in `Stim8hr` but not significant in `Stim48hr`. Can you
conclude that its biological effect differs between the two conditions? What analysis would be
needed?

Write your answer before running the scaffold.
"""
        ),
        code(
            """
exercise_3 = {
    "conclusion": (
        "No. A significant result and a non-significant result do not themselves establish "
        "a significant difference between conditions."
    ),
    "needed_analysis": (
        "Test the perturbation-by-condition interaction, or an equivalent prespecified contrast "
        "of effect estimates, with uncertainty and multiplicity correction."
    ),
    "why": (
        "The estimates can be similar while their standard errors or statistical power differ."
    ),
}
exercise_3
"""
        ),
        markdown(
            """
## Step 8 - Descriptive polarization-model annotation

The fourth source table contains the authors' regulator coefficients for polarization signatures.
The workflow filters that table to source-QC-pass genes and adds two membership flags. These
coefficients are **official descriptive annotations** from the same study: this project does not
refit the model, and their agreement with a candidate rank is not independent validation. They
are not inputs to `priority_score`.
"""
        ),
        code(
            """
polarization = pd.read_csv(TABLE_DIR / "candidate_polarization_coefficients.csv")
polarization_columns = [
    "regulator",
    "dataset_key",
    "signature",
    "coef_mean",
    "coef_sem",
    "coef_rank",
    "in_top_candidates_by_condition",
    "in_cross_condition_candidates",
]
display(polarization[polarization_columns].head(20))
"""
        ),
        markdown(
            """
## Step 9 - Donor-matched IL10 and IL21 follow-up

The arrayed follow-up is a separate, smaller evidence layer. The source columns are percentages
for IL10 and IL21. For each donor and perturbation, the workflow subtracts the matched
non-targeting-control mean percentage from the observed percentage:

```text
donor delta (percentage points) = observed perturbation percentage - matched donor NTC mean
```

Matching within donor removes the donor's baseline level from the descriptive comparison. It
does not create extra donors, and it does not prove mechanism. The summary intentionally reports
descriptive mean, median, minimum, and maximum deltas without p-values.
"""
        ),
        code(
            """
donor_deltas = pd.read_csv(TABLE_DIR / "validation_donor_deltas.csv")
delta_columns = ["IL10_delta_vs_donor_NTC", "IL21_delta_vs_donor_NTC"]
validation_columns = [
    column
    for column in [
        "sample",
        "donor",
        "perturbation",
        "control_n",
        "IL10_perc",
        "IL10_control_mean",
        "IL10_delta_vs_donor_NTC",
        "IL21_perc",
        "IL21_control_mean",
        "IL21_delta_vs_donor_NTC",
    ]
    if column in donor_deltas.columns
]
display(donor_deltas[validation_columns].sort_values(["perturbation", "donor"]))
"""
        ),
        code(
            """
validation_summary = pd.read_csv(TABLE_DIR / "validation_summary.csv")
display(validation_summary)
display(Image(filename=FIGURE_DIR / "04_arrayed_validation_deltas.png", width=1000))
"""
        ),
        markdown(
            """
### Exercise 4 - Judge direction and consistency

For one perturbation, ask whether IL10 and IL21 deltas have the same sign in every donor. Then
separate three ideas: direction, magnitude, and uncertainty. A consistent descriptive direction
is encouraging, but the number of donors still limits precision.
"""
        ),
        code(
            """
# Answer scaffold: change this if you want to inspect another perturbation.
chosen_perturbation = donor_deltas["perturbation"].iloc[0]
chosen = donor_deltas.query("perturbation == @chosen_perturbation")
exercise_4 = {
    "perturbation": chosen_perturbation,
    "n_donors": chosen["donor"].nunique(),
    "all_positive_by_readout": {
        column: bool((chosen[column] > 0).all()) for column in delta_columns
    },
    "all_negative_by_readout": {
        column: bool((chosen[column] < 0).all()) for column in delta_columns
    },
    "uncertainty_statement": "TODO: explain why these descriptive deltas are not a p-value.",
}
exercise_4
"""
        ),
        markdown(
            """
## Step 10 - Read the generated report and methods

The report leads with the result and limitations. The methods record the exact filters and score
definition. Treat these as auditable outputs, not replacements for inspecting the tables above.
"""
        ),
        code(
            """
display(Markdown((OUTPUT_DIR / "report.md").read_text(encoding="utf-8")))
"""
        ),
        code(
            """
display(Markdown((OUTPUT_DIR / "methods.md").read_text(encoding="utf-8")))
"""
        ),
        markdown(
            """
## Common pitfalls

| Pitfall | Better interpretation or fix |
|---|---|
| Treating 22 million cells as 22 million independent experiments | The design has four donors; cells and guides are nested measurements. |
| Calling source-reported cross-donor/guide metrics independently reproduced | Say they were imported and audited from the authors' processed tables. |
| Calling `n_downstream` biological impact | It is the authors' 10% FDR discovery count and depends on power. |
| Scoring before quality gates | Apply eligibility gates first and preserve the failure ledger. |
| Calling a composite score a probability or p-value | It is a geometric mean of three within-condition percentile ranks. |
| Claiming context specificity from significant versus non-significant results | Fit a perturbation-by-condition interaction or direct contrast. |
| Pooling donor-matched deltas as independent technical replicates | Summarize by donor and report the small biological sample size. |
| Calling study-model coefficients independent validation | They are descriptive source annotations; this project does not refit them. |
| Calling IL10/IL21 follow-up target validation | Describe it as donor-matched, descriptive corroboration of selected readouts. |
"""
        ),
        markdown(
            """
## Extensions for a stronger project

1. **Independent cell-level recomputation:** download a tractable subset of the `.h5ad` files,
   rerun guide QC and donor-aware effect estimation, then compare with source-reported values.
2. **Prespecified component sensitivity:** before viewing results, define a leave-one-component-out
   check and report whether conclusions depend entirely on one source-reported metric.
3. **Formal condition interaction:** estimate perturbation-by-condition contrasts with donor and
   guide structure, then correct across tested interactions.
4. **Orthogonal validation:** confirm target knockdown and cytokine/state changes with an assay
   not used in the screen, ideally in new donors.
5. **Mechanistic follow-up:** test whether the candidate changes helper-T-cell polarization or
   function, not only IL10/IL21 abundance.
"""
        ),
        markdown(
            """
## Final teach-back

Explain this chain aloud without looking back:

> official processed tables -> source audit -> hard eligibility gates -> within-condition
> percentiles -> transparent geometric-mean rank -> descriptive cross-condition robustness ->
> descriptive polarization annotation -> donor-matched IL10/IL21 follow-up -> qualified claim
> and next experiment

Then answer:

1. Which metrics were independently recomputed, and which were source-reported?
2. Why is `n_downstream` power-dependent?
3. Why do hard filters precede the composite score?
4. Why is significant versus non-significant not an interaction test?
5. What would turn this target triage into stronger causal evidence?
"""
        ),
        code(
            """
# Final answer scaffold: fill this in using your own words.
teach_back = {
    "recomputed_here": [],
    "source_reported": [],
    "n_downstream_power_dependence": "",
    "hard_gates_before_ranking": "",
    "interaction_test_boundary": "",
    "next_causal_experiment": "",
}
teach_back
"""
        ),
    ]

    for index, cell in enumerate(notebook.cells):
        cell.id = f"official-{index:02d}"
        cell.metadata = {}
        if cell.cell_type == "code":
            cell.execution_count = None
            cell.outputs = []

    notebook.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    }
    nbformat.write(notebook, NOTEBOOK)


if __name__ == "__main__":
    main()
