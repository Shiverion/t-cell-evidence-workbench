# Step-by-Step: Lab Track Walkthrough (First-Timer)

A sequential runbook for **Built with Claude: Life Sciences** (Anthropic + Gladstone Institutes
+ Cerebral Valley), **July 7-13, 2026, global virtual**. Built for someone new to the domain,
targeting the **Lab Track** with **near-full-time** availability.

Your setup: **Claude subscription (Max), not API.** You run everything off the subscription —
Claude Science (web workbench) and Claude Code. The $200 API credits only matter if you write
programmatic API calls, which the Lab Track does not require. The limit to respect is Max's
usage windows, so schedule heavy compute deliberately (see Stage 2).

## The one idea that matters for you

> **Claude Science can run the entire analysis. Your job is to understand it well enough to
> defend it.** For the Lab Track, the deliverable is a *reproducible analysis or trained model*
> that answers a biological question — and the learning (and the credibility) is entirely in the
> interpretation, not the execution. So the tags below flip the usual hackathon logic: the
> *running* is delegated, the *understanding* is the manual work you came for.

### The Understand-It Loop (do this for EVERY figure/table Claude Science produces)

1. Read Claude Science's plain-language description of what it did and why.
2. Close it. **Restate the result in your own words** without looking. If you can't, you don't
   understand it yet.
3. Predict: "if the biology is what I think, this figure should show ___."
4. Check the figure against your prediction.
5. If it doesn't match, ask Claude Science *"why?"* and dig until it does.

Do not advance to the next step until you've closed this loop on the current output. This loop
IS the Lab Track learning. Everything else is scaffolding.

## How to read the tags

- **[AI]** — let Claude Science / Claude Code do it; you review.
- **[HYBRID]** — AI assists, but the decision or the understanding is yours.
- **[MANUAL]** — you do it; delegating skips the learning or needs your judgment.

"Ask Claude Science:" and "Ask Claude Code:" lines are copy-paste prompts. Replace `{...}`.

---

## Stage 0 — Before July 7 (prep: use July 5-6)

### 0.1 Confirm you're in and tools work — **[MANUAL]**
- [ ] **Apply if you haven't — applications close ~July 5 (today).** Top 500 get 1 month Claude
      Max 20x + $200 credits.
- [ ] Confirm you can open **Claude Science** and that it loads (macOS/Linux, or remote via SSH).
- [ ] Confirm **Claude Code** works and, if you have it, the `bio-research` plugin skills are
      available (`/bio-research:start`, `/bio-research:single-cell-rna-qc`, etc.).
- Why manual: money, credentials, and access. Find dead tools now, not on day one.

### 0.2 Biology crash course, aimed at your dataset — **[HYBRID]**
- [ ] Learn core vocabulary, tilted toward **immunology + single cell** (T cells, immune
      response, gene expression, cell types).
- Ask Claude Code: *"You are my biology tutor for a single-cell immunology hackathon. Explain
  T cells and their subtypes, what single-cell RNA sequencing measures, and what a 'cell type'
  and a 'marker gene' are — each in 3 sentences at a software-engineer level. Then quiz me."*
- Do MANUALLY: **write a 20-term glossary in your own words.** Copy-pasting definitions teaches
  you nothing.

### 0.3 Learn the single-cell pipeline shape — **[HYBRID]** *(this is what lets you read the output)*
- [ ] Understand the canonical scRNA-seq workflow at a conceptual level, because you must
      interpret each stage's output:
  1. **QC** — drop bad cells (low genes, high mitochondrial %). Output: filtering stats.
  2. **Normalization** — make cells comparable.
  3. **Dimensionality reduction + clustering** — group similar cells. Output: **UMAP** plot.
  4. **Cell-type annotation** — label clusters by marker genes. Output: labeled UMAP.
  5. **Differential expression** — what genes differ between groups. Output: **volcano plot** / gene lists.
- Ask Claude Code (if you have the plugin): run `/bio-research:single-cell-rna-qc` and
  `/bio-research:scvi-tools` and read what each stage checks for and why.
- Do MANUALLY: for each of the 5 stages, write one sentence on **what its output figure means
  and what "good" looks like.** You will stare at these exact figures all week.

### 0.4 Choose dataset + biological question — **[HYBRID] then [MANUAL] decision**
- **Recommended dataset: immune T-cell sequencing** (single cell). It has the most learnable,
  best-documented pipeline and interpretable outputs (cell types, marker genes), and Claude
  Science is pre-configured for single-cell. Alternatives: *DNA regulatory activity prediction*
  (a "trained model" task — more ML, subtler biology) and *protein interaction networks* (graph
  analysis) — both harder to interpret as a first-timer.
- Ask Claude Code (if available): `/bio-research:scientific-problem-selection` to pressure-test
  candidate questions.
- Do MANUALLY: **write ONE specific biological question**, e.g. *"Which T-cell subtypes differ
  between condition A and B, and which marker genes drive that difference?"* A Lab Track
  submission answers a question; "I analyzed the data" is not a question. This choice is yours.

---

## Stage 1 — Day 1 (Mon Jul 7): Orient

### 1.1 Read the dataset documentation — **[MANUAL]**
- [ ] Read the data dictionary: what each file/column is, how the data was generated, sample
      count, and any known caveats the organizers flag.
- Why manual: **you cannot interpret an output whose input you don't understand.** This is the
  foundation of the whole week.

### 1.2 Load and first-look in Claude Science — **[HYBRID]**
- Ask Claude Science: *"Load this T-cell single-cell dataset. Give me summary stats (cells,
  genes, samples), a QC overview (genes/cell, mitochondrial %), and flag anything unusual.
  Show the code you ran."*
- Do the Understand-It Loop on the QC overview before continuing.

### 1.3 Lock the question and success criterion — **[MANUAL]**
- [ ] Write, in one paragraph: the biological question, what a **credible answer** looks like,
      and how you'd know if the result is wrong. Pin it where you'll see it daily.
- Why manual: this is your compass. If Claude Science wanders, this pulls it back.

---

## Stage 2 — Days 2-4 (Tue-Thu): Analyze — AI runs it, you understand it

> Pace heavy compute against your Max usage window: kick off the big run, then spend the cooldown
> doing the Understand-It Loop on what already finished.

### 2.1 Run the pipeline — **[AI]**
- Ask Claude Science: *"Run the standard single-cell workflow to answer my question: QC ->
  normalization -> clustering -> cell-type annotation -> differential expression between
  {group A} and {group B}. Produce a figure per stage, keep every artifact reproducible with
  its code, and use the reviewer agent to check the calculations."*
- Why AI: this is exactly what Claude Science is built for (end-to-end, reproducible artifacts).

### 2.2 Understand every stage's output — **[MANUAL]** *(THE CORE OF YOUR WEEK)*
- [ ] Run the **Understand-It Loop** on each artifact: QC stats, UMAP, annotated UMAP, volcano
      plot / DE gene list.
- [ ] For the annotated UMAP: **pick 2 cell types and name the marker genes that justify the
      label.** Ask Claude Science *"why is this cluster called a CD8 T cell?"* and check the
      markers are real (CD8A, etc.).
- [ ] For the DE result: **pick the top 3 genes and look up what they do** (use the PubMed /
      Consensus MCP or Claude Science's databases). Can you tell a biological story?
- Why manual: this is the learning you signed up for. If you skip it, you have an analysis you
  can't explain — which a Lab Track judge (or any scientist) will see through instantly.

### 2.3 Sanity-check and reproduce — **[HYBRID]**
- [ ] Re-run one stage with a different parameter (e.g. clustering resolution) and see whether
      your main finding survives. If it flips, your result is fragile — note that.
- Ask Claude Science: *"Re-run clustering at resolution 0.5 and 1.0 and tell me if my key
  cell-type difference holds."*
- Do MANUALLY: **verify one result by hand** — e.g. confirm a claimed marker gene is actually
  high in that cluster. Don't let the reviewer agent be your only check.

### 2.4 Iterate the question — **[MANUAL]**
- [ ] Biology is iterative. If the data answered your question or surprised you, sharpen or pivot
      the question. Record why.

---

## Stage 3 — Days 5-6 (Fri-Sat): Interpret and package

### 3.1 Interpret the biology — **[MANUAL]** *(the heart of the deliverable)*
- [ ] Write the **biological claim** your analysis supports, in plain language, in your own
      words. Not "cluster 4 is upregulated" but "T-cell subtype X shifts toward an exhausted
      state in condition B, driven by genes Y and Z."
- Why manual: the claim is the point. AI can describe the figure; only you can commit to what it
  *means* and stake the submission on it.

### 3.2 Ground it in the literature — **[HYBRID]**
- Ask Claude Code: *"Search PubMed and Consensus: is it known that {my finding} occurs in {my
  condition}? Give me supporting and contradicting papers with citations."*
- Do MANUALLY: **decide what's known vs. novel vs. uncertain.** That judgment is yours; the
  search is the AI's.

### 3.3 Build the reproducibility package — **[AI]**
- Ask Claude Science: *"Bundle the full analysis: code, environment, and figures, so someone
  can reproduce it from raw data. Generate a plain-language methods section from the message
  history."*
- [ ] **Verify it actually reproduces** — this is your check, not a claim to take on faith.

### 3.4 State uncertainty and limitations — **[MANUAL]**
- [ ] Write what you are NOT sure about: batch effects, small sample size, parameter
      sensitivity, annotations you couldn't confirm.
- Why manual: honest limitations are what make a scientist trust the work. Judges reward it;
  first-timers usually skip it.

---

## Stage 4 — Day 7 (Sun Jul 13): Submit and present

### 4.1 Plain-language summary — **[HYBRID]**
- Ask Claude Science: *"Draft a summary of my analysis: question, method, result, biological
  interpretation, limitations — from the reproducible artifacts and message history."*
- Do MANUALLY: **rewrite the claims in your voice** and cut anything you can't personally defend.

### 4.2 Demo / walkthrough recording — **[HYBRID]**
- Ask Claude Science: *"Draft a 3-minute walkthrough script: the question, the key UMAP and
  volcano figures, the biological finding, and why it's reproducible."*
- Do MANUALLY: record it. Practice explaining one figure with no notes — if you can, you've
  learned it.

### 4.3 Final submission — **[MANUAL]**
- [ ] Submit the reproducible analysis + summary per the event's requirements. Double-check the
      package opens and runs from scratch.

---

## Stage 5 — After: lock in the learning — **[HYBRID / MANUAL]**

### 5.1 The "can I explain it?" retro — **[MANUAL]**
- [ ] Success gate for a learning-first Lab Track: **can you now walk someone through the whole
      pipeline — QC to biological claim — from memory, and defend each choice?** If yes, you met
      your goal regardless of placement. If a stage is fuzzy, that's your next study target.

### 5.2 Pattern + insight catalog — **[HYBRID]**
- Ask Claude Code: *"From my notes, draft a catalog: the analysis pattern I used, where
  deterministic tooling ended and the AI's judgment began, how results were verified, the
  failure modes, and how this reproducible-analysis pattern transfers to legal / finance / cyber
  evidence work."*
- Do MANUALLY: **the transfer insights and the biology you learned are yours** — edit heavily.

---

## One-glance summary

| Do it yourself (manual) | Let AI drive |
|---|---|
| Apply, confirm access, credentials | Load data, run QC and stats |
| Understand biology; write your glossary | Explain concepts, quiz you |
| Read the dataset documentation | Run the full single-cell pipeline |
| Lock the biological question | Produce reproducible artifacts + methods text |
| **Understand every output (Understand-It Loop)** | Draft plain-language descriptions |
| Verify a result by hand | Re-run with different parameters |
| Commit to the biological claim | Search literature for support/contradiction |
| State uncertainty and limitations | Bundle the reproducibility package |
| The "can I explain it?" retro | Draft the summary and demo script |
| Transfer insights to other domains | Structure the pattern catalog |

Rule of thumb for the Lab Track: **Claude Science runs the experiment; you own the question,
the interpretation, and the honesty about what you don't know.**
