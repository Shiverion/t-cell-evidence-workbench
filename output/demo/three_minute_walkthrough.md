# Three-minute walkthrough script

**0:00–0:25 — The decision problem**

“This project helps a scientist decide which computational hits deserve expensive follow-up.
This is simulated teaching data, so none of the biology shown is a real discovery. The key promise is not automated biological validation. It is an auditable separation
between
a fast cell-level signal and a stricter donor-level recomputation.”

**0:25–0:55 — Input and guardrails**

“I preserved raw integer counts, locked the CD8 gate and six-gene exhaustion panel before looking
at results, and treated donors—not individual cells—as biological replicates. Normalized values
were used only for visualization and module scoring.”

**0:55–1:25 — UMAP and annotation**

“The first figure shows marker-defined CD8 states. UMAP is a map of local expression similarity,
not proof of cell types. I checked that each label is supported by its registered marker panel.”

**1:25–1:55 — Headline score result**

“After averaging the exhaustion score per donor and subtype, the result was terminally_exhausted, with a donor-mean score change of 1.886 and FDR 0.000271.
The robustness result was stable at every registered resolution,
so I retain the headline claim.”

**1:55–2:30 — Gene-level recomputation**

“The volcano uses counts summed per donor and a count-aware PyDESeq2 model. The reviewer then took
the naive per-cell hits and asked whether their direction and FDR survived pseudobulk. 24
audited hits did not survive; that difference is the pseudoreplication lesson.”

**2:30–3:00 — Boundary and takeaway**

“A hit is only labeled verified here when donor-level statistics agree and a human-auditable
PubMed/Open Targets record passes. Even then, verified means computationally corroborated—not
wet-lab validated. The reusable pattern is to aggregate to the true unit of independence and let
an independent recomputation overturn the fast first pass.”
