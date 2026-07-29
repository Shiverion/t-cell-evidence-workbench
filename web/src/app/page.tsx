import {
  ArrowRight,
  CheckCircle,
  Flask,
  GitBranch,
  SlidersHorizontal,
} from "@phosphor-icons/react/ssr";
import Link from "next/link";

import { FunnelChart } from "@/components/funnel-chart";
import {
  Eyebrow,
  Metric,
  PrimaryLink,
  SectionHeader,
  StatusBadge,
} from "@/components/ui";
import { conditionLabel, formatInteger, formatScore } from "@/lib/format";
import {
  getBundleFingerprint,
  getDashboardData,
  getManifest,
} from "@/lib/data";
import { CONDITIONS } from "@/lib/types";

export default async function HomePage() {
  const [{ runSummary, funnel, topCandidates, crossCandidates }, manifest] =
    await Promise.all([getDashboardData(), getManifest()]);
  const bundleFingerprint = getBundleFingerprint();
  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(manifest.generatedAtUtc));
  const allScreenRows = funnel
    .filter((row) => row.stageOrder === 0)
    .reduce((total, row) => total + row.nRows, 0);
  const eligibleRows = Object.values(runSummary.sourceQcPassesByCondition).reduce(
    (total, value) => total + value,
    0,
  );
  const lead = runSummary.leadCrossConditionCandidate;
  const primaryGene =
    lead?.gene ?? crossCandidates[0]?.gene ?? topCandidates[0]?.gene ?? null;

  return (
    <>
      <section
        id="review-overview"
        data-review-target="overview"
        tabIndex={-1}
        className="scroll-mt-24 grid gap-8 border-b border-line pb-10 outline-none lg:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.65fr)] lg:items-end"
      >
        <div className="pt-2">
          <Eyebrow>Registered CD4+ Perturb-seq analysis</Eyebrow>
          <h1 className="max-w-4xl text-4xl font-semibold leading-[0.98] tracking-[-0.055em] text-ink sm:text-5xl lg:text-[4.2rem]">
            Follow the evidence from screen row to next experiment.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-ink-soft">
            Inspect why a perturbation passed, compare its behavior across conditions, and
            document a claim without crossing the project&apos;s inference boundary.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            {primaryGene ? (
              <PrimaryLink href={`/genes/${primaryGene}`}>
                Open {primaryGene} dossier
              </PrimaryLink>
            ) : null}
            <Link
              href="/explore"
              className="inline-flex min-h-10 items-center gap-2 px-2 text-sm font-semibold text-accent-dark hover:text-ink"
            >
              Explore all candidates
              <ArrowRight aria-hidden="true" size={17} />
            </Link>
          </div>
        </div>

        <aside className="paper-surface border border-line bg-surface p-5 sm:p-6">
          <div className="flex items-center justify-between gap-4 border-b border-line pb-4">
            <div>
              <p className="text-xs font-medium text-ink-faint">Analysis contract</p>
              <p className="mt-1 text-sm font-semibold text-ink">Pinned default run</p>
            </div>
            <StatusBadge tone="success">
              <CheckCircle aria-hidden="true" size={12} weight="fill" className="mr-1" />
              {runSummary.status}
            </StatusBadge>
          </div>
          <dl className="mt-5 space-y-4 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Conditions</dt>
              <dd className="font-mono text-xs text-ink">Rest · 8 h · 48 h</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Hard gates</dt>
              <dd className="font-mono text-xs text-ink">6 registered</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Ranking</dt>
              <dd className="text-right font-mono text-xs text-ink">Within condition</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Claim level</dt>
              <dd className="text-right font-mono text-xs text-ink">Source-QC candidate</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Generated</dt>
              <dd>
                <time
                  dateTime={manifest.generatedAtUtc}
                  className="font-mono text-xs text-ink"
                >
                  {generatedAt} UTC
                </time>
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-soft">Manifest</dt>
              <dd>
                <Link
                  href="/provenance"
                  title={`Analysis bundle SHA-256 ${bundleFingerprint}`}
                  className="font-mono text-xs text-accent-dark hover:text-ink"
                >
                  sha256 {bundleFingerprint.slice(0, 12)}…
                </Link>
              </dd>
            </div>
          </dl>
        </aside>
      </section>

      <section
        aria-label="Run metrics"
        className="grid gap-px border-b border-line bg-line sm:grid-cols-2 xl:grid-cols-4 [&>*]:bg-canvas"
      >
        <div className="sm:pr-6">
          <Metric
            label="Source rows audited"
            value={formatInteger(allScreenRows)}
            detail="Perturbation-condition results"
          />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Eligible rows"
            value={formatInteger(eligibleRows)}
            detail="Across all three conditions"
          />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Cross-condition genes"
            value={formatInteger(runSummary.crossConditionCandidateCount)}
            detail="Passed every gate in all conditions"
          />
        </div>
        <div className="sm:pl-6">
          <Metric
            label="Leading reproducible candidate"
            value={lead?.gene ?? "None"}
            detail={
              lead
                ? `Worst-condition score ${formatScore(lead.minPriorityScore)}`
                : "No cross-condition candidate"
            }
          />
        </div>
      </section>

      <section className="mt-12 grid gap-10 xl:grid-cols-[minmax(0,1.18fr)_minmax(22rem,0.82fr)]">
        <div>
          <SectionHeader
            title="Condition leaders"
            description="The top registered source-QC candidates within each culture condition."
            trailing={
              <Link href="/compare" className="text-sm font-semibold text-accent-dark hover:text-ink">
                Compare genes
              </Link>
            }
          />
          <div className="border-y border-line bg-surface/45">
            <div className="grid grid-cols-[minmax(6rem,1fr)_3.5rem_5rem] gap-3 border-b border-line px-3 py-2 font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint sm:grid-cols-[minmax(8rem,1fr)_8rem_5rem_7rem_7rem]">
              <span>Gene</span>
              <span className="hidden sm:block">Condition</span>
              <span>Rank</span>
              <span className="text-right">Score</span>
              <span className="hidden text-right sm:block">Donor min</span>
            </div>
            {CONDITIONS.flatMap((condition) =>
              topCandidates
                .filter((row) => row.cultureCondition === condition)
                .slice(0, 3)
                .map((row) => (
                  <Link
                    key={`${condition}-${row.gene}`}
                    href={`/genes/${row.gene}`}
                    className="grid min-h-12 grid-cols-[minmax(6rem,1fr)_3.5rem_5rem] items-center gap-3 border-b border-line/70 px-3 text-sm last:border-0 hover:bg-accent-soft/50 sm:grid-cols-[minmax(8rem,1fr)_8rem_5rem_7rem_7rem]"
                  >
                    <span className="font-semibold text-ink">{row.gene}</span>
                    <span className="hidden text-xs text-ink-soft sm:block">
                      {conditionLabel[condition]}
                    </span>
                    <span className="numeric font-mono text-xs text-ink-soft">
                      #{row.rankWithinCondition}
                    </span>
                    <span className="numeric text-right font-mono text-xs text-ink">
                      {formatScore(row.priorityScore)}
                    </span>
                    <span className="numeric hidden text-right font-mono text-xs text-ink-soft sm:block">
                      {formatScore(row.crossdonorMin)}
                    </span>
                  </Link>
                )),
            )}
          </div>
        </div>

        <div>
          <SectionHeader
            title="Registered filter funnel"
            description="Counts decrease as each non-negotiable source-QC gate is applied."
          />
          <FunnelChart rows={funnel} />
        </div>
      </section>

      <section className="mt-14 border-t border-line pt-9">
        <SectionHeader
          title="Three ways into the analysis"
          description="Choose the task that matches the decision you need to make."
        />
        <div className="grid gap-px overflow-hidden border border-line bg-line md:grid-cols-[1.15fr_0.9fr_1fr]">
          {[
            {
              href: "/explore",
              icon: Flask,
              title: "Find a candidate",
              body: "Filter the eligible universe by gene, condition, score, and reproducibility status.",
            },
            ...(primaryGene
              ? [
                  {
                    href: `/genes/${primaryGene}`,
                    icon: GitBranch,
                    title: "Trace the evidence",
                    body: "Move from a gene to condition results, source annotations, follow-up, and provenance.",
                  },
                ]
              : []),
            {
              href: "/robustness",
              icon: SlidersHorizontal,
              title: "Challenge the ranking",
              body: "Reweight the score components and inspect which conclusions remain stable.",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="group min-h-52 bg-surface p-6 hover:bg-accent-soft/45"
              >
                <Icon aria-hidden="true" size={24} className="text-accent" />
                <h3 className="mt-10 text-lg font-semibold tracking-[-0.025em] text-ink">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-ink-soft">{item.body}</p>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-accent-dark">
                  Open workspace
                  <ArrowRight
                    aria-hidden="true"
                    size={16}
                    className="transition-transform group-hover:translate-x-1"
                  />
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mt-12 flex flex-col justify-between gap-5 border-y border-line-strong bg-surface-strong px-6 py-7 text-ink sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
            Interpretation boundary
          </p>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
            These are source-QC prioritization results. They are not independent verification,
            experimental validation, causal proof, or therapeutic recommendations.
          </p>
        </div>
        <StatusBadge tone="accent">{crossCandidates.length} reproducible candidates</StatusBadge>
      </section>
    </>
  );
}
