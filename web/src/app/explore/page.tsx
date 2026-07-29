import type { Metadata } from "next";

import { CandidateExplorer } from "@/components/candidate-explorer";
import { PageHeader, StatusBadge } from "@/components/ui";
import { getCandidates, getCrossCandidates } from "@/lib/data";

export const metadata: Metadata = {
  title: "Candidate explorer",
};

export default async function ExplorePage() {
  const [candidates, crossCandidates] = await Promise.all([
    getCandidates(),
    getCrossCandidates(),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Candidate explorer"
        title="Search the complete eligible universe."
        description="Every row shown here passed all six registered source-QC gates. Filter and sort without hiding the component metrics behind the priority score."
        action={<StatusBadge tone="accent">{candidates.length.toLocaleString()} rows</StatusBadge>}
      />
      <CandidateExplorer
        rows={candidates}
        crossConditionGenes={crossCandidates.map((row) => row.gene)}
      />
    </>
  );
}
