# Claude Science Hackathon Learning Plan

> **Event:** Built with Claude: Life Sciences (Anthropic + Gladstone Institutes + Cerebral Valley) | **Dates:** July 7-13, 2026 | **Format:** global virtual, week-long | **Tracks:** Lab (Claude Science) and Development (Claude Code) | **My track:** Lab Track — executable runbook in [STEP_BY_STEP.md](./STEP_BY_STEP.md)

Goal: use this hackathon as a learning lab (not a prize competition) to understand how frontier AI is applied to scientific research, and to extract reusable architecture patterns for other high-stakes domains: legal, finance, cybersecurity, and autonomous agents. Success = insight gained.

## Phase 0: Logistics (before the event)

1. Apply on time: applications close ~July 5. Top 500 applicants get 1 month of Claude Max 20x + $200 API credits.
2. Access (subscription, not API): confirm Claude Science opens and Claude Code works off your Max subscription; note Max usage windows so you can pace heavy compute. The $200 API credits only matter if you write programmatic API calls.
3. Environment: open Claude Science and confirm it loads the provided datasets; if using Claude Code, confirm the `bio-research` plugin skills and MCP servers are available. Smoke-test one real query.
4. Data: the organizers provide real datasets (immune T-cell sequencing, DNA regulatory activity prediction, protein interaction networks) — plan around these, not a self-staged corpus.
5. Team (virtual): as a non-biologist, find at least one biologist/domain collaborator in the event's online channels. A solo SWE will misframe the biology.
6. Submission: it is a week-long virtual event — reserve the final day for the reproducible package, a plain-language summary, and a short recorded walkthrough.

## Learning Objectives

Each objective ends in a checkable artifact. By event end I have produced all of them.

1. Agent vs. pipeline judgment: a one-paragraph written answer to "why does this system need an agent/verification loop instead of a deterministic pipeline?", grounded in >=2 demos I actually saw.
2. Biology fluency: a running glossary with >=20 terms I can define in one sentence without lookup.
3. Database tooling: the completed Day-3 MCP tool-drill table (6 tools: PubMed, Consensus, ChEMBL, ClinicalTrials.gov, bioRxiv, Open Targets).
4. Scientific AI workflows: the annotated scientific-work chain (Phase 3) marking where AI is deployed today vs. not trusted.
5. Observed architectures: filled-in Observation Checklist for >=3 demos/teams.
6. My own build: a working, reproducible deliverable for my track (Lab: an analysis answering one biological question; Development: the Evidence Comparison Agent) plus a completed self-evaluation.
7. Reusable patterns: a Pattern Catalog of 3-5 rows, each mapped to legal / finance / cyber / agents.
8. Networking: >=1 substantive conversation with a working scientist and >=1 with an AI builder, each captured as a follow-up contact.

## Operating Principles

- Learn the workflow before choosing the architecture.
- Prefer narrow, evidence-heavy problems over broad assistant experiences.
- Treat citations, provenance, and uncertainty as product requirements.
- Ask why a system was designed a certain way, not only what it does.
- Optimize for reusable patterns, not domain trivia.
- Do not ingest patient-identifiable or restricted data into external model calls; confirm any provided dataset's license and de-identification status before use.
- Treat generative bio content with a do-no-harm filter: synthesize published evidence, do not propose novel harmful protocols, and frame any experiment-suggestion output as decision support requiring expert review.

## Phase 1: Preparation

Budget: 12 focused hours, tilted toward tooling (that is where reusable architecture insight comes from).

- Bio crash course: 3h (Days 1-2 compressed into one block).
- AI ecosystem + hands-on MCP database drill (Day 3): 4h.
- Paper sampling (Phase 2): 3h.
- Build-environment + logistics setup: 2h.

### Biomedical Crash Course (3h)

Goal: become dangerous enough to follow conversations. You are not becoming a biologist.

Core vocabulary:

- DNA, RNA, proteins, genes, cells.
- Mutation / variant (modern usage prefers "variant"; e.g. SNP, indel).
- Central dogma: DNA -> RNA -> protein (with known exceptions: reverse transcription in retroviruses, functional non-coding RNAs -- do not state it as absolute).
- Drug discovery pipeline; protein structures; literature reviews; reproducibility and evidence quality.
- Clinical trial phases: Phase 1 (safety/dose, tens), Phase 2 (efficacy signal, hundreds), Phase 3 (confirmatory vs standard of care, hundreds-thousands, basis for approval), Phase 4 (post-market). Approval != completing Phase 3 -- a regulator must still act.
- Biomarkers: a measurable indicator; distinguish prognostic (predicts outcome regardless of treatment) vs predictive (predicts response to a treatment) vs surrogate endpoint (a biomarker standing in for a clinical outcome -- often contested).

Resources if needed: Crash Course Biology, Khan Academy, short visual explainers for protein structure and gene expression. Skim; do not study.

### AI Ecosystem Preparation + MCP Database Drill (4h)

#### Claude primitives, tied to a build decision

Review each primitive as a decision for the citation-grounded build, not as a generic topic:

- Tool use / MCP: the 6 bio MCP servers are your retrieval layer.
- Subagents: one lightweight subagent per paper for extraction, main loop for synthesis (parallelism + cost).
- Long context + prompt caching: load 5-8 full papers once, cache the prefix, ask many questions cheaply.
- Extended/adaptive thinking: for the contradiction-detection step.
- Structured outputs: force per-paper extraction into a fixed schema so the report is not free text.
- Server-side web_search / web_fetch: for sources with no MCP server.
- Open Targets is essentially a production knowledge-graph of target-disease-drug evidence -- query it as a live GraphRAG example before reading about GraphRAG abstractly.

Confirm current Anthropic feature names/availability against the docs the week of the event -- names and limits change. (Computer use is out of scope; GraphRAG is relevant only to the rejected Option 2.)

#### Working answer to the agent-vs-pipeline question (refine at the event)

A deterministic pipeline wins when the schema is fixed and inputs are clean: SQL over ClinicalTrials.gov fields, exact-match ID lookups in ChEMBL. The LLM/agent earns its place only where you need:

- (a) normalization across heterogeneous free text (matching a claim in paper A to a differently-worded contradicting claim in paper B);
- (b) open-ended tool routing (deciding whether a question needs PubMed vs ChEMBL vs trials without hardcoding);
- (c) synthesis with provenance (a claim plus its source span).

If a step is none of these, keep it deterministic. Reusable rule for legal/finance/cyber: LLM at the fuzzy edges, deterministic code in the middle, human at the sign-off. Treat this as a hypothesis to validate against the demos.

#### Day 3: MCP Database Drill (hands-on)

These databases are live in your Claude Code session as MCP servers -- do not read about them, query them. Run one real query against each and log (a) an example call, (b) the fields it returns, (c) whether it returns full text or metadata + provenance/citation fields, (d) one limitation.

1. PubMed / PubMed Central: `search_articles` + `get_full_text_article` on a hackathon-theme term.
2. Consensus: `search` the same question; compare its synthesized, cited answer vs raw PubMed hits.
3. ChEMBL: `compound_search` + `get_mechanism` for a known drug (e.g. imatinib). Key quantities: potency (IC50/Ki/EC50 -- lower = more potent), mechanism of action, ADMET. The MCP here is ChEMBL v34; public release moves (v35+), so never hardcode a version.
4. ClinicalTrials.gov: `search_trials` + `get_trial_details` / `analyze_endpoints` for one condition.
5. bioRxiv/medRxiv: `search_preprints` by category + date for recent theme preprints.
6. Open Targets: `search_entities` + one `query_open_targets_graphql` for a gene-disease association.

Deliverable: a half-page table of tool / example call / returned fields / one gotcha. This IS the retrieval layer for your build -- you are testing your tools, not studying reference material.

Reference-only (no MCP tool in this environment): UniProt (protein sequence/function, uniprot.org) and PDB (3D structures, rcsb.org). Skip unless the theme is structural biology.

## Phase 2: Research Paper Sampling (3h)

Do not master the literature. Aim for fluency + one reusable architecture idea.

Read 6 papers, timeboxed to 3 hours total:

- 2 review papers (skim for vocabulary).
- 2 AI-for-science papers (read for architecture / eval).
- 2 hackathon-theme biology papers.

Use the PubMed / Consensus / bioRxiv MCP tools to FIND and triage these papers, and prefer papers you can pull full text for so reading doubles as tool practice.

For each paper: abstract (what problem?), figures (central evidence?), methods (data and tools?), discussion (limitations?), references (important prior work?). Skip heavy math unless it affects architecture or evaluation.

## Phase 3: Mental Model of Scientific Work

Scientific work usually follows this chain:

```text
Idea
-> Literature search
-> Existing evidence
-> Hypothesis
-> Experiment design
-> Experiment execution
-> Results
-> Analysis
-> Publication
-> Peer review
-> Future research
```

This is idealized -- real loops iterate and fail. For this hackathon, mark where AI is deployed today (literature search, hypothesis generation, structure/property prediction, analysis) vs. where it is not trusted (experiment execution, final clinical decisions). The interesting architecture questions live at those boundaries.

For each step, ask: What information is needed? What tools are already used? What is slow, repetitive, or error-prone? What must remain under human control? What would make the output trustworthy?

## Observation Checklist

Cap ~15 questions total so it is usable live. Use when watching demos, talking with teams, or evaluating your own build.

### Architecture

- Why use Claude/an LLM here, and where does deterministic software stop and the LLM begin?
- Single-agent, multi-agent, or pipeline -- and if subagents, how is the work split?
- MCP servers or hand-rolled API clients -- why?

### Data & Retrieval

- Where does the data come from, and is it structured, unstructured, multimodal, or mixed?
- Retrieval type: keyword, dense, hybrid, graph, or citation-based -- and at what granularity (doc/section/passage/figure/table)?
- Are citations verified against source text, and does the system retrieve contradictions/negative evidence?

### Agent Design

- What tools can the agent use, and is there a plan step and a verification loop?
- How did you control token cost over long context -- caching, context editing, or re-retrieval?
- What should never be delegated to the model?

### Evaluation

- How is correctness measured (precision, recall, coverage, novelty, speed), and is there a benchmark or expert review?
- Are outputs scored for faithfulness and citation accuracy, and does the system expose uncertainty?

### Product

- What painful manual step is being replaced, who is the daily user, and what are the existing alternatives?
- What failed, and what was the biggest challenge?
- What would need to change before a scientist used this seriously?

### Conversation Strategy

Target at least one working scientist and one AI builder. Lead with a specific observation about their demo, not a generic question. Ask scientists what part of their workflow they would never delegate to a model and why -- this surfaces the human-in-the-loop boundary. Capture a contact/follow-up for the strongest conversation.

## Project Strategy

Avoid: another general chatbot; a simple "ask my PDFs" app; generic RAG without a scientific workflow; a demo that cannot explain provenance, uncertainty, or evaluation.

Prefer: a narrow workflow tool; a system that compares evidence rather than only summarizing it; a tool that exposes contradictions and confidence; a project that teaches a reusable architecture pattern.

### Project Selection Filter

Choose a project only if you can answer yes to most of these:

- Does it solve one clear scientific pain point?
- Can it be demoed with public or provided data?
- Can the system show its evidence, and can a human check the output?
- Does it teach something about Claude, agents, retrieval, or evaluation?
- Can a narrow version be built during the hackathon?
- Is the data I plan to use licensed and free of PHI/PII for this use?

## Candidate Projects

> **Track note:** You are targeting the **Lab Track** (analyze the provided datasets with Claude
> Science) — the executable runbook is [STEP_BY_STEP.md](./STEP_BY_STEP.md). The options below are
> the **Development Track** alternative (build a tool with Claude Code); keep them as a fallback or
> a possible second-track idea.

### Committed default: Evidence Comparison Agent

One agent, two input modes that share retrieval + extraction plumbing:

- Fixed paper set -> compare directly. **This is the committed hackathon MVP.**
- Open question -> retrieve-then-compare. **This is the fallback/stretch mode.**

Output: consensus points, contradictions, evidence quality, methods, limitations -- each grounded in a source span.

Why: clear demo, easier to evaluate than open-ended generation, strong fit for long context + structured extraction, and it generalizes to legal, finance, policy, and cybersecurity research. Risk: needs a disciplined schema and careful citation verification so the output is not a generic summary. Commit to this build before arriving, not on-site.

Rejected for hackathon scope: **GraphRAG** (graph build too large); **Experiment Planning** (needs expert validation, and experiment suggestions carry a do-no-harm burden).

## Recommended Build

### Minimum viable demo (5-8 papers)

- Retrieval: pull 5-8 papers via PubMed `search_articles` + `get_full_text_article` (fall back to bioRxiv `get_preprint` for preprints).
- Extraction: one subagent per paper with a structured-output schema `{claim, method, dataset, effect_direction, limitation, source_span}`.
- Cost control: load all papers once into a prompt-cached context.
- Synthesis: group by consensus vs disagreement on `effect_direction`; each report row links back to the `source_span` its claim came from (citation verification = re-check the span exists in the source).
- Uncertainty column: flag rows where papers disagree or extraction confidence is low.

### Go/No-Go and Fallback

By ~1/3 of build time I must have papers loading via an MCP and one paper's claims extracted with a working source link. If not, drop to the fallback: a single-paper claim-and-limitation extractor with verified citations (no cross-paper comparison). The core learning goal -- retrieval + structured extraction + citation grounding -- is fully met by the fallback. A working narrow demo beats a broken broad one.

### Self-Evaluation of My Build

This is a primary insight artifact, not an afterthought:

- (a) Pick 5 papers with a known agreement/disagreement I can verify by hand.
- (b) Does every extracted claim link to a clickable source passage?
- (c) Count hallucinated or unsupported claims out of total.
- (d) Does the uncertainty column actually vary across papers, or is it cosmetic?
- (e) Would I trust this output enough to cite it?
- Record the failure modes.

## Engineering Topics -- study only if it blocks the build

Tied to the Evidence Comparison Agent:

- Citation-aware / hybrid retrieval.
- Claim + contradiction extraction.
- Faithfulness + citation-accuracy evaluation.
- Structured-output schema design.

(Skip ontologies / RDF / OWL / OBO unless a demo makes it relevant. Retrieval and reasoning primitives already covered under AI Ecosystem Preparation.)

## Daily Reflection

At day's end, answer three fast questions that roll up into the Pattern Catalog:

1. One surprise.
2. One pattern worth stealing.
3. One sharper question for tomorrow.

## Post-Hackathon Synthesis (the single success gate)

Success = this Pattern Catalog plus a <=1-page memo within 48h naming the best architecture observed and why, the one most reusable pattern with a concrete mapping to legal OR finance OR cyber, one surprising workflow insight, and the strongest project idea worth continuing.

### Pattern Catalog (target 3-5 rows)

Each row uses a fixed schema:

| Pattern name | Problem it solves | Where deterministic code ends / LLM begins | Retrieval strategy | Verification / eval method | Failure mode | Transfer note (legal / finance / cyber / agents) |
|---|---|---|---|---|---|---|
| | | | | | | |

### Backlog -- study after the event

Deferred until the event surfaces which of these actually matter:

- Knowledge representation: knowledge graphs, ontologies, OBO Foundry, RDF/OWL, biomedical entity normalization, metadata design.
- Retrieval: dense, sparse, hybrid, citation-aware, scientific search, passage/table/figure retrieval.
- Reasoning: multi-step reasoning, planning, reflection, verification, claim extraction, contradiction detection.
- Evaluation: hallucination detection, faithfulness, citation accuracy, benchmarking, human/expert review workflows.

## Final Mindset

Leave with one new architecture, one reusable pattern, one meaningful conversation, and one project idea worth pursuing, and the hackathon has succeeded.
