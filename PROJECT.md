# Project Brief: Verified CD8+ T-cell Exhaustion Triage

Lab Track project for **Built with Claude: Life Sciences** (July 7-13, 2026). Companion to the
[learning plan](./CLAUDE_SCIENCE_HACKATHON_LEARNING_PLAN.md) and the
[step-by-step runbook](./STEP_BY_STEP.md).

**One line:** answer a specific CD8+ T-cell exhaustion question on the provided scRNA-seq data,
then wrap the analysis in an independent verification loop that reports which hits actually
survive a stricter, donor-aware recomputation.

---

## Intended user and positioning (read this before you build anything)

Getting this right matters more than any single figure: it decides what you claim, and what a
scientist or judge will believe.

### Who it is for

**The person deciding where to spend expensive experimental effort** — a computational biologist,
or a wet-lab scientist working alongside one, who has a single-cell dataset and needs to know
*which few candidates out of many are worth committing wet-lab time to.* They can run a pipeline;
what they lack is time and a trustworthy way to separate real signal from statistical artifacts.

You are building the **guardrails / trust layer**, not a domain-expert-for-experts. That plays to
your actual strength (software engineering) and to your meta-goal (a reusable verification pattern
for legal / finance / cyber), and it is a claim a first-time non-biologist can credibly make.

### What it is / what it is NOT

- **It IS:** a reproducible first-pass analysis + a triage tool that ranks candidate hits by
  whether they survive an independent, stricter recomputation, each with provenance.
- **It is NOT:** a "hand us your data and trust the hits" black box. It does not replace a
  computational biologist's judgment; it makes that judgment faster and its inputs auditable.
- **It is NOT** a discovery engine. The goal is rigor and honesty on a known biological axis
  (exhaustion), not a novel finding.

### What "verified" means here (and why not "validated")

In biology, **"validated" means orthogonal experimental confirmation** — qPCR, flow cytometry, a
functional assay. No in-silico pipeline can produce validated hits, and claiming it does is the
fastest way to lose every scientist in the room.

This project uses **"verified"** with a precise, narrow definition:

> A hit is **verified** if it (1) is recomputed with matching sign and adjusted p < 0.05 as
> **donor-level pseudobulk** DE (the statistically correct unit), AND (2) passes a **literature /
> target plausibility** check via PubMed + Open Targets.

That is corroboration and triage, not proof. Use the words **verified / corroborated /
prioritized**; reserve **validated** for the wet lab. Naming this boundary correctly is itself a
signal that you understand the domain.

---

## The science: the specific problem

> **Caveat:** exact dataset fields are unknown until day 1. The Day-1 Data Inspection (below)
> decides the statistical path and which contrast you run. The problem is designed to adapt.

**Question.** In the provided T-cell scRNA-seq data, restricted to CD8+ T cells (CD8A/CD8B+,
CD4-), is a coordinated **exhaustion module score** (over `PDCD1, HAVCR2, LAG3, TOX, TIGIT,
ENTPD1`) significantly higher in **condition B than condition A**, and **which annotated CD8+
subtype** (effector / effector-memory / terminally exhausted) carries the largest up-shift?

**Exact answer.** The single subtype with the largest positive delta in mean exhaustion score
(B minus A) at FDR < 0.05, plus its top driver genes ranked by pseudobulk log2FC.

**Answering output (the four figures/tables that constitute the deliverable):**
1. Annotated CD8+ subtype **UMAP**.
2. Per-subtype exhaustion-score **violin**, split by condition, with the donor-aware p-value.
3. Per-subtype **volcano** (B vs A) over the exhaustion panel.
4. A 4-row **robustness table**: for the headline subtype, does the sign + FDR hold across Leiden
   resolutions 0.4 / 0.6 / 0.8 / 1.0?

**Fallback if only one condition exists:** replace the B-vs-A axis with an
**exhausted-vs-naive/effector** contrast defined by marker thresholds, keeping the identical
score / stratify / sweep structure.

---

## The build arc (near full-time, one week)

Two projects that share a dataset, layered so you get all three goals — learn the biology, ship a
defensible result, and build the reusable pattern.

- **Days 2-4 - the analysis (learn + defensible headline).** Build the CD8+ exhaustion analysis
  above. This is where you learn to read single-cell output.
- **Days 5-6 - the verification loop (the reusable pattern + demo differentiator).** Wrap the
  analysis in a **Reviewer-in-the-Loop**: an independent-recomputation step that takes the top ~30
  genes a naive per-cell Wilcoxon test calls differential, and audits them via (1) donor-level
  pseudobulk recomputation, (2) a pseudoreplication delta (how far the per-cell p-value collapses
  once donors, not cells, are the unit), (3) a PubMed + Open Targets plausibility check.
  Headline number: **N of 30 per-cell hits that failed donor-level verification.**

**Requires donor replicates (>= ~4-6 per condition).** If Day 1 shows no donor labels, ship the
analysis alone with the pseudoreplication caveat stated plainly, and skip the reviewer loop.

---

## Day-by-day plan (July 7-13)

- **Day 1 (Mon) - orient + branch.** Run the Day-1 Data Inspection; commit the statistical path
  and contrast; QC + one baseline clustering; confirm a CD8+ population separates.
- **Days 2-4 (Tue-Thu) - analysis.** Gate CD8+, score exhaustion, annotate subtypes with the
  pre-registered panel, run the condition contrast, build the four deliverable figures + the
  resolution robustness table. Run the Understand-It Loop on every output.
- **Days 5-6 (Fri-Sat) - verification loop + interpretation.** Build the reviewer step; produce
  the verified-findings table; ground survivors in literature; write the biological claim,
  uncertainty, and limitations.
- **Day 7 (Sun) - package + submit.** Reproducible bundle, plain-language summary, 3-minute
  recorded walkthrough.

---

## Day-1 Data Inspection (this picks your branch)

Before any analysis, load the data in Claude Science and record:

- [ ] `adata.obs.columns` and `value_counts` on each candidate label column.
- [ ] **Condition:** are there >= 2 conditions? What are A and B *biologically* (chronic/tumor vs
      healthy? timepoints? tissues?) - this decides whether a directional exhaustion claim is even
      justified, or whether you keep it neutral / use the marker fallback.
- [ ] **Replicates:** do donor / sample / batch IDs exist? -> **pseudobulk primary** if yes;
      **Wilcoxon-exploratory + pseudoreplication caveat** if no. Cross-tab condition x donor for
      confounding.
- [ ] **Genes:** are symbols present (not only Ensembl IDs)? Are `CD8A, CD8B, CD4, PDCD1, HAVCR2,
      LAG3, TOX, TIGIT, ENTPD1` in `var_names`?
- [ ] **Write down the committed decision:** statistical path + contrast + whether the reviewer
      loop is in scope. Pin it where you will see it all week.

---

## Pre-registered specs (lock these BEFORE looking at results)

Locking these prevents post-hoc / cherry-picked conclusions - the thing reviewers attack.

- **CD8 gate:** `CD8A` or `CD8B` positive AND `CD4` negative (excludes CD4 and ambient contamination).
- **Exhaustion panel:** `PDCD1, HAVCR2, LAG3, TOX, TIGIT, ENTPD1`, scored with `sc.tl.score_genes`
  using control-gene binning.
- **Subtype marker panel** (label clusters by these, not by eyeballing):
  - Memory / stem-like: `TCF7, IL7R, SELL, CCR7`
  - Effector / cytotoxic: `GZMB, PRF1, NKG7, GZMK`
  - Terminally exhausted: `TOX, PDCD1, HAVCR2, ENTPD1, LAYN`
- **Statistical unit:** donor-level pseudobulk (aggregate counts per donor x subtype;
  DESeq2/edgeR-style) is the primary test. Per-cell Wilcoxon is exploratory only.
- **Robustness:** Leiden resolutions 0.4 / 0.6 / 0.8 / 1.0; headline claim must hold across all four.
- **Reviewer "verified" rule:** matching sign + pseudobulk adjusted p < 0.05 AND literature/target
  plausibility.

---

## Risks and mitigations

- **Pseudoreplication** (per-cell test on a few donors inflates significance). -> Gate the headline
  on donor pseudobulk; if no donors, flag Wilcoxon as exploratory in plain language.
- **Condition mismatch** (A/B not exhaustion-relevant). -> Inspect Day 1; keep the marker-defined
  exhausted-vs-naive fallback; stay neutral about direction unless labels justify it.
- **Annotation subjectivity** (mislabeling a cluster invalidates the headline). -> Pre-registered
  marker panel + CD8 gate purity check.
- **Score confounded by depth / cell cycle.** -> Control-gene binning, QC on counts/mito, confirm
  the delta survives depth regression, report per-gene log2FC alongside the module score.
- **Scope creep** (sweep x subtypes x fallback x reviewer). -> Timebox to ONE headline subtype for
  the deep dive; keep the sweep a compact 4-row table; reviewer loop only if donors exist.

---

## Alternatives and decision rule

| Project | Dataset | Pick it if |
|---|---|---|
| **Reviewer-in-the-Loop DE** (as the headline, not an add-on) | T-cell scRNA-seq | You want the generator->verifier architecture itself as the trophy AND Day 1 shows >= 4-6 donors/condition. |
| **PPI disease-module test** (real module vs degree-preserving null) | Protein network | You'd rather do graph analysis or want the purest null-model lesson. |
| **Leakage-proof enhancer benchmark** (small CNN vs k-mer baseline, chromosome-held-out split) | DNA regulatory | You specifically want a trained-model deliverable and eval rigor as the transferable skill. |

**Rule:** default to the combined arc above. No donor labels -> analysis-only with the marker
fallback. Want networks -> PPI module. Want a model artifact -> enhancer benchmark. If the
"wet-lab hands data, trusts output" *product* experience is what you actually want, that is the
**Development Track** - reconsider the track before July 7, not during.

---

## Reusable engineering pattern (the transfer payoff)

**Separate a claim from the knobs that produced it, aggregate to the true unit of independence
before believing a p-value, and let an independent recomputation (not a second opinion) overturn a
fast first pass.**

- **Legal:** a clause-risk signature re-checked against the source paragraph, robust to chunk size.
- **Finance:** a fraud-feature shift tested per-account (not per-transaction), recomputed from
  primary filings.
- **Cyber:** an attack-behavior signature across host groups, robust to the clustering threshold,
  confirmed against threat-intel before escalation.
- **Agents:** self-critique that re-derives a result rather than re-asserting confidence.

---

## Submission checklist

- [ ] Reproducible Claude Science package: code + pinned environment + full message history.
- [ ] The four deliverable figures/tables (UMAP, exhaustion violin, volcano, robustness table).
- [ ] Verified-findings table (if reviewer loop in scope): gene | per-cell log2FC & p_adj |
      pseudobulk log2FC & p_adj | CONFIRMED/REFUTED | citation.
- [ ] Plain-language write-up: every QC threshold, the pre-registered decisions, the biological
      claim, and an explicit uncertainty/limitations section.
- [ ] Correct language throughout: verified / corroborated / prioritized - never "validated".
- [ ] 3-minute recorded walkthrough.
