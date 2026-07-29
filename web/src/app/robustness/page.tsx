import type { Metadata } from "next";

import { RobustnessLab } from "@/components/robustness-lab";
import { PageHeader } from "@/components/ui";
import { getCandidates } from "@/lib/data";

export const metadata: Metadata = {
  title: "Robustness lab",
};

export default async function RobustnessPage() {
  const candidates = await getCandidates();

  return (
    <>
      <PageHeader
        eyebrow="Robustness lab"
        title="See which priorities survive a different emphasis."
        description="Reweight the three score components and compare the resulting order with the pinned default run. This is a sensitivity view, not a replacement analysis."
      />
      <RobustnessLab candidates={candidates} />
    </>
  );
}
