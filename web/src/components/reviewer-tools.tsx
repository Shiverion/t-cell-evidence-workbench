"use client";

import { ReviewerFeedback } from "@/components/reviewer-feedback";
import { ReviewerTour } from "@/components/reviewer-tour";

export function ReviewerTools({
  defaultGene,
  bundleFingerprint,
  generatedAtLabel,
  feedbackEmail,
}: {
  defaultGene: string | null;
  bundleFingerprint: string;
  generatedAtLabel: string;
  feedbackEmail?: string;
}) {
  return (
    <div
      aria-label="Reviewer tools"
      className="reviewer-tools-dock fixed z-20 flex max-w-[calc(100vw-2rem)] gap-2"
    >
      <ReviewerTour defaultGene={defaultGene} />
      <ReviewerFeedback
        bundleFingerprint={bundleFingerprint}
        generatedAtLabel={generatedAtLabel}
        feedbackEmail={feedbackEmail}
      />
    </div>
  );
}
