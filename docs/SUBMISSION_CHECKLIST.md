# Official-data submission checklist

Use this checklist for the Primary Human CD4+ T Cell Perturb-seq project. The synthetic CD8+
teaching run is not a substitute for any item below.

## Source and provenance

- [ ] Confirm the event links to the Primary Human CD4+ T Cell Perturb-seq dataset.
- [ ] Read the Virtual Cells Platform dataset card and authors' data-sharing README.
- [ ] Confirm the dataset version, MIT License, and stated no-PII status.
- [ ] Use the commit-pinned public URLs recorded in `configs/official_cd4.yaml`.
- [ ] Preserve the downloader's expected byte lengths and SHA-256 checks.
- [ ] Record the exact input hashes, configuration, code revision, and run timestamp.
- [ ] State that the workflow uses summary tables rather than approximately 1.58 TiB of cell-level
  matrices.

## Reproduce the official run

- [ ] From a clean environment, run `uv sync --extra dev`.
- [ ] Run `uv run perturbseq-triage all --data-dir data/official --output-dir output/official`.
- [ ] Confirm the dataset audit has no blocker.
- [ ] Confirm 33,983 initial perturbation-condition rows.
- [ ] Confirm conditions are exactly `Rest`, `Stim8hr`, and `Stim48hr`.
- [ ] Confirm sample metadata contains four donors and 12 donor-condition rows.
- [ ] With the default 100-cell gate, confirm final pass counts are 497 Rest, 593 Stim8hr, and 562
  Stim48hr.
- [ ] Confirm 224 genes pass source QC in all three conditions and SETDB1 has the leading minimum
  condition score (approximately 0.915).
- [ ] Run the test suite and lint checks.
- [ ] Execute `notebooks/02_cd4_perturbseq_official_tutorial.ipynb` from start to finish with no
  cell errors.

## Audit the triage contract

- [ ] Confirm the screen funnel applies these exact gates:
  `ontarget_significant == True`, `ontarget_effect_size < 0`, `offtarget_flag == False`,
  `n_cells_target >= 100`, positive nonmissing `crossdonor_correlation_min`, and positive
  nonmissing `crossguide_correlation`.
- [ ] Confirm missing, zero, and negative correlations fail the relevant gate.
- [ ] Confirm the final funnel count equals the full triaged-table row count.
- [ ] Confirm percentile ranks are calculated separately within condition.
- [ ] Manually recompute the geometric-mean score for at least one candidate per condition.
- [ ] Confirm the presentation shortlist can be traced back to the full eligible table.
- [ ] Ask a computational biologist to review the gates, source-field meanings, and ranking
  heuristic.

## Interpret the metrics honestly

- [ ] Describe `n_downstream` as the authors' 10% FDR discovery count, excluding on-target effect.
- [ ] State that `n_downstream` depends on power and cell count and is not an effect size.
- [ ] Describe donor and guide correlations as author-reported source statistics.
- [ ] State that this summary workflow does not independently recompute those correlations.
- [ ] Describe `offtarget_flag == False` as "not flagged by the source field," not
  "off-target-free."
- [ ] Describe `priority_score` as a relative prioritization heuristic, not a probability or p-value.

## Cross-condition and arrayed follow-up

- [ ] Treat Rest/Stim8hr/Stim48hr rank differences as descriptive.
- [ ] State that no perturbation-by-condition interaction model was fitted.
- [ ] Describe candidate polarization coefficients as authors' model outputs joined for context.
- [ ] Do not claim that the coefficient join independently reproduces a polarization effect.
- [ ] Keep missing condition entries visible rather than converting them to poor scores or zeros.
- [ ] For IL-10/IL-21, confirm controls are donor matched and labels beginning with `NTC` are
  combined correctly.
- [ ] Confirm missing donor-perturbation pairs are not imputed.
- [ ] Show donor counts and heterogeneity for every arrayed summary.
- [ ] Call the IL-10/IL-21 section "descriptive arrayed follow-up," even though the source filename
  contains `validation`.
- [ ] Do not add post-hoc confirmatory tests after inspecting the follow-up plot.

## Claims and limitations

- [ ] Use "source-QC candidate" or "prioritized candidate" for a condition-specific row.
- [ ] Reserve "reproducible candidate" for a gene that passes every gate in all three conditions.
- [ ] Do not use "verified" or "validated" for a result from this workflow.
- [ ] Do not call a candidate a drug target without separate functional, safety, and druggability
  evidence.
- [ ] State the four-donor generalization limit.
- [ ] State the source-summary and 10% FDR limitations.
- [ ] State that a 100-cell minimum does not equalize statistical power.
- [ ] State that positive correlations can still be weak or uncertain.
- [ ] State that cross-condition plots are not interaction tests.
- [ ] State that the selected, uneven IL-10/IL-21 follow-up is descriptive.
- [ ] Have a T-cell/domain scientist review the biological interpretation.

## Package and present

- [ ] Include the dataset audit, funnel, full triaged table, per-condition shortlist,
  cross-condition table, candidate polarization annotations, arrayed donor deltas/summary,
  figures, report, and provenance.
- [ ] Open every CSV and image and check labels, units, sorting, and missing-value rendering.
- [ ] Rewrite the plain-language result in your own voice.
- [ ] Explain one candidate's three score components without notes.
- [ ] Explain one failed row's exclusion reason without implying biological irrelevance.
- [ ] Practice the claim boundary and the answer to "Was this independently validated?"
- [ ] Reproduce the package from a fresh clone or clean environment once.
- [ ] Record the walkthrough yourself.

## Keep the legacy demo separate

- [ ] Label `output/demo/` and the CD8+ notebook as **SIMULATED - NOT BIOLOGICAL EVIDENCE**.
- [ ] Do not combine synthetic CD8+ figures or numbers with the official CD4+ results.
- [ ] Do not say the synthetic dataset came from the hackathon organizers.
- [ ] If the demo is shown to teach a method, explain why it answers a different biological
  question.
