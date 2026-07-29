import type { Metadata } from "next";

import { FindingCardBuilder } from "@/components/finding-card-builder";
import { EmptyState, PageHeader } from "@/components/ui";
import {
  getCandidates,
  getCrossCandidates,
  getGeneNames,
  getValidationSummaries,
} from "@/lib/data";

export const metadata: Metadata = {
  title: "Finding cards",
};

export default async function FindingsPage({
  searchParams,
}: {
  searchParams: Promise<{ gene?: string | string[] }>;
}) {
  const [{ gene }, candidates, crossCandidates, validations, geneNames] = await Promise.all([
    searchParams,
    getCandidates(),
    getCrossCandidates(),
    getValidationSummaries(),
    getGeneNames(),
  ]);
  const queryGene = Array.isArray(gene) ? gene[0] : gene;
  const requestedGene = queryGene?.trim().toUpperCase();
  const leadingGene = crossCandidates
    .slice()
    .sort((left, right) => left.crossConditionRank - right.crossConditionRank)[0]?.gene;
  const defaultGene =
    requestedGene && geneNames.includes(requestedGene)
      ? requestedGene
      : (leadingGene ?? geneNames[0] ?? "");

  return (
    <>
      <PageHeader
        eyebrow="Finding cards"
        title="Turn an exploration into a reviewable claim."
        description="Build a structured Markdown finding with supporting evidence, explicit limitations, evidence gaps, and a next experiment. The language is intentionally constrained by the analysis contract."
      />
      {defaultGene ? (
        <FindingCardBuilder
          key={defaultGene}
          candidates={candidates}
          crossCandidates={crossCandidates}
          validations={validations}
          geneNames={geneNames}
          defaultGene={defaultGene}
        />
      ) : (
        <EmptyState
          title="No eligible candidates"
          description="This analysis bundle contains no source-QC candidate rows from which to prepare a finding."
        />
      )}
    </>
  );
}
