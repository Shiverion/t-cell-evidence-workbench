import type { Metadata } from "next";

import { GeneComparison } from "@/components/gene-comparison";
import { PageHeader } from "@/components/ui";
import { getCandidates, getCrossCandidates, getGeneNames } from "@/lib/data";

export const metadata: Metadata = {
  title: "Compare genes",
};

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ genes?: string | string[] }>;
}) {
  const [{ genes }, candidates, crossCandidates, geneNames] = await Promise.all([
    searchParams,
    getCandidates(),
    getCrossCandidates(),
    getGeneNames(),
  ]);
  const requestedGenes = (Array.isArray(genes) ? genes.join(",") : (genes ?? ""))
    .split(",")
    .map((gene) => gene.trim().toUpperCase())
    .filter((gene) => geneNames.includes(gene))
    .filter((gene, index, values) => values.indexOf(gene) === index)
    .slice(0, 5);
  const rankedFallbacks = crossCandidates
    .slice()
    .sort((left, right) => left.crossConditionRank - right.crossConditionRank)
    .map((row) => row.gene);
  const defaultGenes = requestedGenes.length
    ? requestedGenes
    : (rankedFallbacks.length ? rankedFallbacks : geneNames).slice(0, 3);

  return (
    <>
      <PageHeader
        eyebrow="Comparison workspace"
        title="Compare candidates without flattening their context."
        description="Review condition-specific scores and source components side by side. Rank differences remain descriptive because this workflow does not fit a perturbation-by-condition interaction."
      />
      <GeneComparison
        key={defaultGenes.join(",")}
        candidates={candidates}
        geneNames={geneNames}
        defaultGenes={defaultGenes}
      />
    </>
  );
}
