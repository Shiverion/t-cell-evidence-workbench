"use client";

import { Check, Copy, DownloadSimple } from "@phosphor-icons/react";
import { useEffect, useMemo, useRef, useState } from "react";

import { StatusBadge } from "@/components/ui";
import { conditionLabel, formatScore } from "@/lib/format";
import type {
  CandidateRow,
  CrossConditionCandidate,
  ValidationSummary,
} from "@/lib/types";

type Finding = {
  title: string;
  claim: string;
  evidence: string[];
  limitations: string[];
  evidenceGap: string;
  nextExperiment: string;
  markdown: string;
};

function buildFinding(
  gene: string,
  candidates: CandidateRow[],
  crossCandidates: CrossConditionCandidate[],
  validations: ValidationSummary[],
): Finding {
  const rows = candidates
    .filter((row) => row.gene === gene)
    .sort((left, right) => left.rankWithinCondition - right.rankWithinCondition);
  const cross = crossCandidates.find((row) => row.gene === gene) ?? null;
  const validation = validations.find((row) => row.perturbation === gene) ?? null;
  const conditionText = rows.map((row) => conditionLabel[row.cultureCondition]).join(", ");
  const claim = cross
    ? `${gene} passed all registered source-QC gates in Rest, 8 h stimulation, and 48 h stimulation and ranked #${cross.crossConditionRank} by its weakest condition priority score. It is a reproducible source-QC candidate for independent follow-up, not an experimentally validated target.`
    : `${gene} passed all registered source-QC gates in ${conditionText}. It is a condition-specific source-QC candidate for independent follow-up, not an experimentally validated target.`;
  const evidence = rows.map(
    (row) =>
      `${conditionLabel[row.cultureCondition]}: rank #${row.rankWithinCondition}, priority score ${formatScore(row.priorityScore)}, minimum donor concordance ${formatScore(row.crossdonorMin)}, and guide concordance ${formatScore(row.crossguide)}.`,
  );
  if (cross) {
    evidence.push(
      `Cross-condition maximin summary: rank #${cross.crossConditionRank}, minimum score ${formatScore(cross.minPriorityScore)}, with ${conditionLabel[cross.worstCondition]} as the lowest-scoring condition.`,
    );
  }
  if (validation) {
    evidence.push(
      `The author-provided descriptive IL-10/IL-21 follow-up contains ${validation.nDonors} observed donors for ${gene}; this is contextual follow-up, not independent confirmation.`,
    );
  }
  const limitations = [
    "The priority score is a relative triage heuristic, not a probability, p-value, or effect size.",
    "Downstream discovery count is power-sensitive, and donor/guide concordance values were reported by the source authors.",
    "Condition rank differences are descriptive because this workflow did not fit a perturbation-by-condition interaction model.",
  ];
  const evidenceGap = validation
    ? "Independent replication, orthogonal perturbation, formal endpoint testing, mechanism, safety, and therapeutic utility remain unestablished."
    : "No matching measurement appears in the selected author-provided IL-10/IL-21 follow-up table. Independent replication, orthogonal perturbation, formal endpoint testing, mechanism, safety, and therapeutic utility remain unestablished.";
  const nextExperiment = cross
    ? `Run an independent multi-donor CRISPRi replication for ${gene} with a prespecified functional endpoint in Rest, 8 h, and 48 h conditions; fit a formal perturbation-by-condition interaction before making a condition-specific claim, then confirm with an orthogonal perturbation.`
    : `Run an independent multi-donor CRISPRi replication for ${gene} in the eligible condition set with a prespecified functional endpoint, then confirm the result with an orthogonal perturbation and targeted mechanism assay.`;
  const title = `${gene} — structured candidate finding`;
  const markdown = [
    `# ${title}`,
    "",
    "## Claim",
    claim,
    "",
    "## Supporting evidence",
    ...evidence.map((item) => `- ${item}`),
    "",
    "## Limitations",
    ...limitations.map((item) => `- ${item}`),
    "",
    "## Evidence gap",
    evidenceGap,
    "",
    "## Recommended next experiment",
    nextExperiment,
    "",
    "> Generated from the pinned T-cell Perturb-seq source-QC artifacts. Review before use.",
  ].join("\n");

  return {
    title,
    claim,
    evidence,
    limitations,
    evidenceGap,
    nextExperiment,
    markdown,
  };
}

export function FindingCardBuilder({
  candidates,
  crossCandidates,
  validations,
  geneNames,
  defaultGene,
}: {
  candidates: CandidateRow[];
  crossCandidates: CrossConditionCandidate[];
  validations: ValidationSummary[];
  geneNames: string[];
  defaultGene: string;
}) {
  const [gene, setGene] = useState(defaultGene);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");
  const copyTimerRef = useRef<number | null>(null);
  const finding = useMemo(
    () => buildFinding(gene, candidates, crossCandidates, validations),
    [candidates, crossCandidates, gene, validations],
  );

  useEffect(
    () => () => {
      if (copyTimerRef.current != null) window.clearTimeout(copyTimerRef.current);
    },
    [],
  );

  async function copyMarkdown() {
    if (copyTimerRef.current != null) window.clearTimeout(copyTimerRef.current);
    try {
      await navigator.clipboard.writeText(finding.markdown);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
    copyTimerRef.current = window.setTimeout(() => setCopyState("idle"), 2400);
  }

  function downloadMarkdown() {
    const blob = new Blob([finding.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${gene.toLowerCase()}-finding-card.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="grid gap-8 xl:grid-cols-[19rem_minmax(0,1fr)]">
      <aside>
        <div className="paper-surface border border-line bg-surface p-5">
          <label className="block">
            <span className="mb-2 block text-xs font-medium text-ink-soft">Candidate gene</span>
            <select
              value={gene}
              onChange={(event) => setGene(event.target.value)}
              className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas px-3 text-sm font-semibold text-ink outline-none focus:border-accent"
            >
              {geneNames.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <p className="mt-4 text-xs leading-5 text-ink-soft">
            The template uses deterministic evidence fields and conservative language. It does not
            ask a language model to infer biology.
          </p>
          <div className="mt-6 space-y-2 border-t border-line pt-5">
            <button
              type="button"
              onClick={copyMarkdown}
              className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-canvas hover:bg-accent-dark"
            >
              {copyState === "copied" ? (
                <Check aria-hidden="true" size={17} />
              ) : (
                <Copy aria-hidden="true" size={17} />
              )}
              {copyState === "copied" ? "Copied" : "Copy Markdown"}
            </button>
            <button
              type="button"
              onClick={downloadMarkdown}
              className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-line-strong bg-canvas px-4 text-sm font-semibold text-ink hover:border-accent"
            >
              <DownloadSimple aria-hidden="true" size={17} />
              Download .md
            </button>
            <p aria-live="polite" className="min-h-5 text-center text-xs text-ink-soft">
              {copyState === "error"
                ? "Clipboard access failed. Use Download .md instead."
                : copyState === "copied"
                  ? "Markdown copied to the clipboard."
                  : ""}
            </p>
          </div>
        </div>
      </aside>

      <article
        id="finding-card"
        data-review-target="finding"
        tabIndex={-1}
        className="paper-surface scroll-mt-24 border border-line bg-surface px-5 py-7 outline-none sm:px-8 sm:py-9"
      >
        <div className="flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-start">
          <div>
            <p className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-accent">
              Review-ready finding
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-ink">
              {finding.title}
            </h2>
          </div>
          <StatusBadge tone="warning">Requires human review</StatusBadge>
        </div>

        <section className="py-7">
          <h3 className="text-sm font-semibold text-ink">Claim</h3>
          <p className="mt-3 max-w-4xl text-base leading-7 text-ink">{finding.claim}</p>
        </section>

        <section className="border-t border-line py-7">
          <h3 className="text-sm font-semibold text-ink">Supporting evidence</h3>
          <ul className="mt-3 divide-y divide-line/75">
            {finding.evidence.map((item) => (
              <li key={item} className="py-3 text-sm leading-6 text-ink-soft">
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="grid gap-7 border-t border-line py-7 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-ink">Limitations</h3>
            <ul className="mt-3 space-y-3">
              {finding.limitations.map((item) => (
                <li key={item} className="text-sm leading-6 text-ink-soft">
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-ink">Evidence gap</h3>
            <p className="mt-3 text-sm leading-6 text-ink-soft">{finding.evidenceGap}</p>
          </div>
        </section>

        <section className="border-t border-line pt-7">
          <h3 className="text-sm font-semibold text-ink">Recommended next experiment</h3>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-ink-soft">
            {finding.nextExperiment}
          </p>
        </section>
      </article>
    </div>
  );
}
