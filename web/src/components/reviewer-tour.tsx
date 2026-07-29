"use client";

import {
  ArrowLeft,
  ArrowRight,
  Check,
  MapTrifold,
  X,
} from "@phosphor-icons/react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

const TOUR_STORAGE_KEY = "t-cell-reviewer-tour-v1";

type TourStep = {
  label: string;
  title: string;
  description: string;
  href: string;
  targetId: string;
  matches: (pathname: string) => boolean;
};

export function ReviewerTour({ defaultGene }: { defaultGene: string | null }) {
  const pathname = usePathname();
  const router = useRouter();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [active, setActive] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const steps = useMemo<TourStep[]>(
    () => [
      {
        label: "Overview",
        title: "Read the registered analysis first.",
        description:
          "Start with the pinned run contract, headline counts, and leading candidate before opening an exploratory view.",
        href: "/#review-overview",
        targetId: "review-overview",
        matches: (value) => value === "/",
      },
      {
        label: "Candidate",
        title: "Inspect the eligible candidate universe.",
        description:
          "Filter perturbation-condition rows and compare the registered score, rank, donor, and guide evidence.",
        href: "/explore#review-candidate",
        targetId: "review-candidate",
        matches: (value) => value === "/explore",
      },
      {
        label: "Evidence graph",
        title: defaultGene
          ? `Trace the evidence lineage for ${defaultGene}.`
          : "Trace a candidate evidence lineage.",
        description:
          "Follow the target through registered results, source annotations, provenance, and explicit evidence gaps.",
        href: defaultGene
          ? `/genes/${defaultGene}#evidence-graph`
          : "/explore#review-candidate",
        targetId: defaultGene ? "evidence-graph" : "review-candidate",
        matches: (value) =>
          defaultGene ? value.startsWith("/genes/") : value === "/explore",
      },
      {
        label: "Finding card",
        title: "Convert evidence into a bounded finding.",
        description:
          "Review a deterministic claim, its supporting evidence, limitations, evidence gap, and next experiment before export.",
        href: defaultGene
          ? `/findings?gene=${encodeURIComponent(defaultGene)}#finding-card`
          : "/findings#finding-card",
        targetId: "finding-card",
        matches: (value) => value === "/findings",
      },
    ],
    [defaultGene],
  );

  const matchedStepIndex = active
    ? steps.findIndex((step) => step.matches(pathname))
    : -1;
  const currentStepIndex =
    matchedStepIndex >= 0 ? matchedStepIndex : stepIndex;

  useEffect(() => {
    try {
      window.sessionStorage.setItem(
        TOUR_STORAGE_KEY,
        JSON.stringify({ active, step: currentStepIndex }),
      );
    } catch {
      // Session persistence is optional.
    }
  }, [active, currentStepIndex]);

  useEffect(() => {
    if (!active) return;
    const timer = window.setTimeout(() => {
      const target = document.getElementById(steps[currentStepIndex].targetId);
      if (!target) return;
      target.focus({ preventScroll: true });
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 180);
    return () => window.clearTimeout(timer);
  }, [active, currentStepIndex, pathname, steps]);

  function openStep(nextIndex: number) {
    const boundedIndex = Math.min(Math.max(nextIndex, 0), steps.length - 1);
    setActive(true);
    setStepIndex(boundedIndex);
    router.push(steps[boundedIndex].href);
  }

  function startTour() {
    openStep(0);
  }

  function exitTour() {
    setActive(false);
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  }

  const step = steps[currentStepIndex];
  const finalStep = currentStepIndex === steps.length - 1;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={startTour}
        aria-expanded={active}
        className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line-strong bg-surface px-3 text-sm font-semibold text-ink shadow-[0_16px_40px_-28px_var(--shadow)] hover:border-accent hover:text-accent-dark"
      >
        <MapTrifold aria-hidden="true" size={18} />
        Guided review
      </button>

      {active ? (
        <aside
          role="dialog"
          aria-modal="false"
          aria-labelledby="reviewer-tour-title"
          aria-describedby="reviewer-tour-description"
          className="reviewer-tour-panel paper-surface fixed z-30 max-h-[calc(100dvh-7rem)] overflow-y-auto border border-line-strong bg-surface p-5"
        >
          <p aria-live="polite" className="sr-only">
            Review step {currentStepIndex + 1} of {steps.length}: {step.label}
          </p>
          <div className="flex items-start justify-between gap-5">
            <div>
              <p className="font-mono text-[0.66rem] font-semibold uppercase tracking-[0.14em] text-accent">
                Step {currentStepIndex + 1} of {steps.length} · {step.label}
              </p>
              <h2
                id="reviewer-tour-title"
                className="mt-3 text-xl font-semibold tracking-[-0.035em] text-ink"
              >
                {step.title}
              </h2>
            </div>
            <button
              type="button"
              onClick={exitTour}
              aria-label="Exit guided review"
              className="grid size-10 shrink-0 place-items-center rounded-lg border border-line bg-canvas text-ink-soft hover:border-accent hover:text-ink"
            >
              <X aria-hidden="true" size={18} />
            </button>
          </div>

          <p
            id="reviewer-tour-description"
            className="mt-3 text-sm leading-6 text-ink-soft"
          >
            {step.description}
          </p>

          <div className="mt-5 flex gap-1.5" aria-hidden="true">
            {steps.map((item, index) => (
              <span
                key={item.label}
                className={`h-1 flex-1 rounded-full ${
                  index <= currentStepIndex ? "bg-accent" : "bg-line-strong"
                }`}
              />
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-4">
            <button
              type="button"
              onClick={() => openStep(currentStepIndex - 1)}
              disabled={currentStepIndex === 0}
              className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm font-semibold text-ink-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-35"
            >
              <ArrowLeft aria-hidden="true" size={16} />
              Previous
            </button>
            <button
              type="button"
              onClick={() =>
                finalStep ? exitTour() : openStep(currentStepIndex + 1)
              }
              className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-canvas hover:bg-accent-dark"
            >
              {finalStep ? (
                <>
                  <Check aria-hidden="true" size={16} />
                  Finish review
                </>
              ) : (
                <>
                  Next: {steps[currentStepIndex + 1].label}
                  <ArrowRight aria-hidden="true" size={16} />
                </>
              )}
            </button>
          </div>
        </aside>
      ) : null}
    </>
  );
}
