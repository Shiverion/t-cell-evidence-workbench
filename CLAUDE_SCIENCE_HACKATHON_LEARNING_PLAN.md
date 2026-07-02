# Claude Science Hackathon Learning Plan

Goal: understand where AI is heading in life sciences, with the hackathon as a learning lab rather than a prize competition.

## Review Summary

The original plan has the right center of gravity: learn how frontier AI is applied to scientific research, observe how researchers work, and extract reusable engineering patterns. The main refinements are:

- Replace broad curiosity with a staged plan: prepare, observe, build, synthesize.
- Turn project ideas into decision criteria so the project does not become a generic chatbot or RAG demo.
- Add concrete questions for researchers, builders, and demos.
- Add evaluation and verification as first-class topics, because scientific AI is only useful when claims can be trusted.
- Correct encoding artifacts and remove symbolic noise so the document is easier to reuse.

## Philosophy

This hackathon is not about becoming a biomedical researcher in a few days.

It is about learning how modern AI systems can support scientific work:

- How researchers form questions, find evidence, and decide what is trustworthy.
- Where deterministic software, retrieval, tools, agents, and human review fit together.
- Which Claude and Anthropic platform patterns are useful for scientific workflows.
- Which architecture patterns are reusable in legal AI, finance AI, cybersecurity, and autonomous agents.

Success is measured by insight gained, not by prizes won.

## Learning Objectives

### Primary Objectives

- Understand the Claude and Anthropic ecosystem for scientific work.
- Learn common biomedical AI workflows at a practical level.
- Understand scientific AI agents, tool use, retrieval, and verification loops.
- Observe how scientists and builders use AI in production or near-production settings.
- Identify reusable engineering patterns for other high-stakes domains.

### Secondary Objectives

- Meet researchers and technical builders.
- Learn enough biology vocabulary to follow conversations.
- Explore real scientific datasets and databases.
- Experiment with new AI tooling.
- Build a small project that teaches something concrete.

## Operating Principles

- Learn the workflow before choosing the architecture.
- Prefer narrow, evidence-heavy problems over broad assistant experiences.
- Treat citations, provenance, and uncertainty as product requirements.
- Ask why a system was designed a certain way, not only what it does.
- Optimize for reusable patterns, not domain trivia.
- Keep a daily record of surprising assumptions, useful architectures, and open questions.

## Phase 1: Pre-Hackathon Preparation

Target time: 8 to 12 focused hours.

### Biomedical Crash Course

Goal: become dangerous enough to understand conversations.

#### Day 1: Biology Basics

Learn:

- DNA
- RNA
- Proteins
- Genes
- Cells
- Mutation
- Central dogma: DNA -> RNA -> protein

Suggested resources:

- Crash Course Biology
- Khan Academy biology modules
- Short visual explainers for protein structure and gene expression

Timebox: 2 hours.

#### Day 2: Biomedical Research Workflow

Learn:

- Drug discovery pipeline
- Clinical trial phases
- Biomarkers
- Protein structures
- Literature reviews
- Reproducibility and evidence quality

Timebox: 2 hours.

#### Day 3: Scientific Databases

Learn what each resource stores and why scientists use it:

- PubMed: biomedical literature
- PubMed Central: full-text biomedical papers where available
- UniProt: protein sequence and function
- Protein Data Bank: 3D protein structures
- ChEMBL: bioactive molecules and drug discovery data
- ClinicalTrials.gov: clinical trial records

Timebox: 2 hours.

### AI Ecosystem Preparation

Read or review:

- Claude API basics
- Tool use
- MCP
- Long context workflows
- Computer use
- Agent skills and agentic orchestration
- Retrieval-augmented generation
- GraphRAG and knowledge graphs

Core question: why would a scientific AI system need Claude or an agent instead of a traditional pipeline?

## Phase 2: Research Paper Sampling

Do not try to master the literature. Learn the workflow and vocabulary.

Read:

- 5 review papers
- 5 AI-for-science papers
- 5 biology or biomedical papers related to the hackathon theme

For each paper, focus on:

- Abstract: what problem is being solved?
- Figures: what evidence is central?
- Methods: what data and tools were used?
- Discussion: what are the limitations?
- References: which papers are treated as important prior work?

Skip heavy mathematical detail at first unless it directly affects architecture or evaluation.

## Phase 3: Mental Model Of Scientific Work

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

For each step, ask:

- What information is needed?
- What tools are already used?
- What is slow, repetitive, or error-prone?
- What must remain under human control?
- What would make the output trustworthy?

## Observation Checklist

Use these questions when watching demos, talking with teams, or evaluating your own project.

### Architecture

- Why use Claude or an LLM here?
- Where does deterministic software stop?
- Where does the LLM begin?
- Which tasks are fully automated?
- Which tasks require human approval?
- Is this a single-agent, multi-agent, or pipeline system?
- What state, memory, or context is preserved across steps?

### Data

- Where does the data come from?
- Is the data structured, unstructured, multimodal, or mixed?
- How is the data validated?
- How noisy or incomplete is it?
- How are conflicting papers or sources handled?
- How are hallucinations, stale facts, and weak citations prevented?

### Retrieval

- Is retrieval keyword-based, dense, hybrid, graph-based, or citation-based?
- Are papers retrieved at the document, section, passage, figure, or table level?
- Are citations verified against source text?
- Does the system retrieve negative evidence and contradictions?
- How are source quality and recency handled?

### Agent Design

- What tools can the agent use?
- Does the agent plan before acting?
- Is there a verification loop?
- Can it recover from failed tool calls?
- Can it run long tasks?
- What gets logged for inspection?
- What should never be delegated to the model?

### Evaluation

- How is correctness measured?
- Is the goal precision, recall, coverage, novelty, or speed?
- Is there a benchmark dataset?
- Is there human expert review?
- Are outputs scored for faithfulness and citation accuracy?
- Does the system expose uncertainty?

### Product

- What problem is actually being solved?
- Who is the daily user?
- What existing workflow is being replaced or accelerated?
- What is the painful manual step?
- What are the existing alternatives?
- What would make a scientist trust or reject this tool?

## Project Strategy

Avoid building:

- Another general chatbot.
- A simple "ask my PDFs" app.
- Generic RAG without a scientific workflow.
- A demo that cannot explain provenance, uncertainty, or evaluation.

Prefer building:

- A narrow workflow tool.
- A system that compares evidence rather than only summarizing it.
- A tool that exposes contradictions and confidence.
- A project that teaches a reusable architecture pattern.

### Project Selection Filter

Choose a project only if you can answer yes to most of these:

- Does it solve one clear scientific pain point?
- Can it be demoed with public or provided data?
- Can the system show its evidence?
- Can the output be checked by a human?
- Does it teach something about Claude, agents, retrieval, or evaluation?
- Can a narrow version be built during the hackathon?

## Candidate Projects

### Option 1: Research Evidence Agent

Input: natural language scientific question.

Workflow:

```text
Question
-> Search literature
-> Retrieve relevant evidence
-> Compare papers
-> Identify agreement
-> Identify contradictions
-> Generate evidence report
```

Why it is useful:

- Shows retrieval, synthesis, contradiction detection, and citation grounding.
- Reusable in legal, finance, policy, and cybersecurity research.

Risk:

- Needs careful citation verification to avoid shallow summaries.

### Option 2: Scientific GraphRAG

Input: paper set or topic.

Workflow:

```text
Papers
-> Extract entities
-> Build knowledge graph
-> Link claims to evidence
-> Query graph
-> Generate grounded reasoning
```

Why it is useful:

- Teaches knowledge representation and graph-based retrieval.
- Useful when relationships matter more than isolated passages.

Risk:

- Graph construction can become too large for a hackathon.

Narrow version:

- Extract entities and relationships from 5 to 10 papers only.

### Option 3: Experiment Planning Assistant

Input: research objective.

Output:

- Related papers
- Existing methods
- Known limitations
- Missing knowledge
- Suggested experiments
- Risks and assumptions

Why it is useful:

- Maps well to real research planning.
- Forces the system to reason over evidence gaps.

Risk:

- Experiment suggestions require expert review and should be framed as planning support, not scientific authority.

### Option 4: Paper Comparison Agent

Input: 10 to 20 papers.

Output:

- Consensus points
- Contradictions
- Evidence quality
- Novel findings
- Methods used
- Limitations

Why it is useful:

- Clear demo.
- Easier to evaluate than open-ended research generation.
- Strong fit for long context and structured extraction.

Risk:

- Needs a disciplined schema so the output does not become a generic summary.

## Recommended Hackathon Build

Best default choice: Paper Comparison Agent.

Reason:

- It is narrow enough for a hackathon.
- It avoids generic chatbot behavior.
- It exercises retrieval, long context, structured extraction, and verification.
- It produces an artifact that scientists can inspect.
- It generalizes to other high-stakes domains.

Minimum viable demo:

- Upload or select 5 to 10 papers.
- Extract claims, methods, datasets, and limitations.
- Group papers by consensus and disagreement.
- Produce a report with citations back to source passages.
- Show an uncertainty or evidence-quality column.

## Things To Learn From Other Teams

Ask every demo:

- Why this architecture?
- Why this model?
- Why this retrieval strategy?
- Why not GraphRAG?
- Why not fine-tuning?
- Why use agents?
- What was the biggest challenge?
- What failed?
- How did you evaluate correctness?
- What would need to change before a scientist used this seriously?

## Engineering Topics To Study

### Knowledge Representation

- Knowledge graphs
- Ontologies
- OBO Foundry
- RDF and OWL basics
- Biomedical entity normalization
- Metadata design

### Retrieval

- Dense retrieval
- Sparse retrieval
- Hybrid search
- Citation-aware retrieval
- Scientific search
- Passage, table, and figure retrieval

### Reasoning

- Multi-step reasoning
- Tool use
- Planning
- Reflection
- Verification
- Claim extraction
- Contradiction detection

### Evaluation

- Hallucination detection
- Faithfulness
- Citation accuracy
- Benchmarking
- Human evaluation
- Expert review workflows

## Daily Reflection Template

At the end of each day, answer:

- What surprised me?
- What assumption was wrong?
- What architecture did I like?
- What architecture did I dislike?
- What would I reuse in my own projects?
- What term, dataset, or workflow do I still not understand?
- What is one sharper question to ask tomorrow?

## Success Criteria

By the end of the hackathon, I should be able to explain:

- Why AI is useful in life sciences.
- How scientists actually use LLMs and AI tools.
- What Claude or Anthropic tooling does differently from a basic pipeline.
- Which architectures are reusable outside biology.
- What production-grade scientific AI needs for trust, evaluation, and review.
- What ideas I can apply to legal AI, finance AI, cybersecurity, and future autonomous agents.

## Post-Hackathon Synthesis

Within 48 hours after the event, write a short memo:

- Best architecture observed.
- Most reusable engineering pattern.
- Most important scientific workflow insight.
- Best conversation.
- Strongest project idea worth continuing.
- One thing to study next.

## Final Mindset

I am not attending this hackathon to become a biomedical researcher.

I am attending to observe the next generation of AI systems.

If I leave with one new architecture, one reusable engineering pattern, one meaningful conversation, and one project idea worth pursuing, the hackathon has succeeded.

