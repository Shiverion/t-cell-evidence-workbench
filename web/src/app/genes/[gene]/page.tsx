import { ArrowLeft, DownloadSimple } from "@phosphor-icons/react/ssr";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EvidenceGraph } from "@/components/evidence-graph";
import { ScoreAnatomy } from "@/components/score-anatomy";
import {
  Metric,
  PageHeader,
  PrimaryLink,
  SectionHeader,
  StatusBadge,
} from "@/components/ui";
import { conditionLabel, formatScore, formatSigned } from "@/lib/format";
import { getGeneDossier } from "@/lib/data";

type GenePageProps = {
  params: Promise<{ gene: string }>;
};

export async function generateMetadata({ params }: GenePageProps): Promise<Metadata> {
  const { gene } = await params;
  return { title: `${gene.toUpperCase()} dossier` };
}

function nullableSigned(value: number | null, digits = 3) {
  return value == null ? "Not reported" : formatSigned(value, digits);
}

export default async function GenePage({ params }: GenePageProps) {
  const { gene } = await params;
  const dossier = await getGeneDossier(gene);
  if (!dossier) notFound();

  const bestCondition = [...dossier.conditionRows].sort(
    (left, right) => left.rankWithinCondition - right.rankWithinCondition,
  )[0];
  const weakestCondition = [...dossier.conditionRows].sort(
    (left, right) => left.priorityScore - right.priorityScore,
  )[0];

  return (
    <>
      <Link
        href="/explore"
        className="mb-5 inline-flex items-center gap-2 text-xs font-semibold text-ink-soft hover:text-accent-dark"
      >
        <ArrowLeft aria-hidden="true" size={14} />
        Candidate explorer
      </Link>

      <PageHeader
        eyebrow="Gene dossier"
        title={dossier.gene}
        description={
          dossier.crossCondition
            ? `${dossier.gene} passed every registered source-QC gate in all three culture conditions. Inspect the evidence lineage before forming a follow-up hypothesis.`
            : `${dossier.gene} has eligible condition-specific results but does not enter the complete three-condition candidate set.`
        }
        action={
          <>
            <StatusBadge tone={dossier.crossCondition ? "accent" : "neutral"}>
              {dossier.crossCondition ? "Reproducible candidate" : "Condition candidate"}
            </StatusBadge>
            <PrimaryLink href={`/findings?gene=${dossier.gene}`}>Draft finding</PrimaryLink>
          </>
        }
      />

      <section
        aria-label="Gene summary"
        className="grid gap-px border-b border-line bg-line sm:grid-cols-2 xl:grid-cols-4 [&>*]:bg-canvas"
      >
        <div className="sm:pr-6">
          <Metric
            label="Eligible conditions"
            value={`${dossier.conditionRows.length} / 3`}
            detail="Registered source-QC pass"
          />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Best within-condition rank"
            value={`#${bestCondition.rankWithinCondition}`}
            detail={conditionLabel[bestCondition.cultureCondition]}
          />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Weakest condition score"
            value={formatScore(weakestCondition.priorityScore)}
            detail={conditionLabel[weakestCondition.cultureCondition]}
          />
        </div>
        <div className="sm:pl-6">
          <Metric
            label="Arrayed follow-up"
            value={dossier.validation ? `${dossier.validation.nDonors} donors` : "Not available"}
            detail="Author-provided descriptive table"
          />
        </div>
      </section>

      <section
        id="evidence-graph"
        data-review-target="evidence"
        tabIndex={-1}
        className="mt-10 scroll-mt-24 outline-none"
      >
        <EvidenceGraph dossier={dossier} />
      </section>

      <section className="mt-12 grid gap-10 xl:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)]">
        <div>
          <SectionHeader
            title="Score anatomy"
            description="Raw source values and their within-condition percentile positions. The score rewards balance across all three components."
          />
          <ScoreAnatomy rows={dossier.conditionRows} />
        </div>
        <aside>
          <SectionHeader
            title="Claim boundary"
            description="What this evidence package can and cannot support."
          />
          <div className="border-y border-line">
            <div className="py-5">
              <StatusBadge tone="success">Supported</StatusBadge>
              <p className="mt-3 text-sm leading-6 text-ink">
                {dossier.gene} passed the registered source-QC gates in{" "}
                {dossier.conditionRows.length === 3
                  ? "all three conditions"
                  : dossier.conditionRows
                      .map((row) => conditionLabel[row.cultureCondition])
                      .join(", ")}
                .
              </p>
            </div>
            <div className="border-t border-line py-5">
              <StatusBadge tone="warning">Not established</StatusBadge>
              <p className="mt-3 text-sm leading-6 text-ink-soft">
                Independent replication, a condition interaction, mechanism, safety, druggability,
                or therapeutic utility.
              </p>
            </div>
            <div className="border-t border-line py-5">
              <StatusBadge tone="neutral">Recommended next evidence</StatusBadge>
              <p className="mt-3 text-sm leading-6 text-ink-soft">
                Independent CRISPRi replication with prespecified functional endpoints across
                donors, followed by orthogonal perturbation and mechanism testing.
              </p>
            </div>
          </div>
        </aside>
      </section>

      <section className="mt-12">
        <SectionHeader
          title="Source polarization annotations"
          description="Coefficients were calculated by the source authors and joined here for context. They are not an independent validation layer."
          trailing={<StatusBadge tone="neutral">{dossier.coefficients.length} shown</StatusBadge>}
        />
        {dossier.coefficients.length ? (
          <div className="overflow-x-auto border-y border-line bg-surface/50">
            <table className="w-full min-w-[720px] border-collapse text-left">
              <thead>
                <tr className="border-b border-line font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint">
                  <th className="px-3 py-3 font-medium">Signature</th>
                  <th className="px-3 py-3 font-medium">Condition</th>
                  <th className="px-3 py-3 text-right font-medium">Coefficient</th>
                  <th className="px-3 py-3 text-right font-medium">SEM</th>
                  <th className="px-3 py-3 text-right font-medium">Source rank</th>
                  <th className="px-3 py-3 font-medium">Regulator context</th>
                </tr>
              </thead>
              <tbody>
                {dossier.coefficients.map((coefficient) => (
                  <tr
                    key={coefficient.datasetKey}
                    className="border-b border-line/75 text-sm last:border-0"
                  >
                    <td className="px-3 py-3 font-medium text-ink">{coefficient.signature}</td>
                    <td className="px-3 py-3 text-ink-soft">{coefficient.celltype}</td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink">
                      {formatSigned(coefficient.coefficientMean, 4)}
                    </td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                      {formatScore(coefficient.coefficientSem, 4)}
                    </td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                      {formatScore(coefficient.coefficientRank)}
                    </td>
                    <td className="px-3 py-3 text-xs text-ink-soft">
                      {coefficient.regulatorType || "Not annotated"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="border-y border-line py-8 text-sm text-ink-soft">
            No matching source polarization coefficient rows were available.
          </p>
        )}
      </section>

      <section className="mt-12">
        <SectionHeader
          title="Descriptive arrayed follow-up"
          description="Percentage-point deltas relative to each donor's available NTC-family mean. No confirmatory p-value was calculated."
          trailing={
            dossier.validation ? (
              <StatusBadge tone="warning">{dossier.validation.nDonors} donors observed</StatusBadge>
            ) : null
          }
        />
        {dossier.validation ? (
          <div className="grid divide-y divide-line border-y border-line sm:grid-cols-2 sm:divide-x sm:divide-y-0">
            <div className="py-6 sm:pr-8">
              <p className="text-xs font-medium text-ink-faint">IL-10 mean delta</p>
              <p className="numeric mt-2 font-mono text-3xl tracking-[-0.04em] text-ink">
                {nullableSigned(dossier.validation.il10MeanDelta)}
                <span className="ml-2 text-xs text-ink-faint">percentage points</span>
              </p>
              <p className="mt-3 text-xs text-ink-soft">
                Observed range {nullableSigned(dossier.validation.il10MinDelta)} to{" "}
                {nullableSigned(dossier.validation.il10MaxDelta)}
              </p>
            </div>
            <div className="py-6 sm:pl-8">
              <p className="text-xs font-medium text-ink-faint">IL-21 mean delta</p>
              <p className="numeric mt-2 font-mono text-3xl tracking-[-0.04em] text-ink">
                {nullableSigned(dossier.validation.il21MeanDelta)}
                <span className="ml-2 text-xs text-ink-faint">percentage points</span>
              </p>
              <p className="mt-3 text-xs text-ink-soft">
                Observed range {nullableSigned(dossier.validation.il21MinDelta)} to{" "}
                {nullableSigned(dossier.validation.il21MaxDelta)}
              </p>
            </div>
          </div>
        ) : (
          <div className="border border-dashed border-warning/45 bg-warning/10 p-6">
            <p className="font-semibold text-ink">No selected arrayed follow-up measurement</p>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
              Absence from this small source table is an evidence gap, not evidence that the
              perturbation lacks a cytokine phenotype.
            </p>
          </div>
        )}
      </section>

      <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6">
        <p className="text-xs text-ink-faint">
          Dossier values are read directly from the pinned generated artifacts.
        </p>
        <Link
          href={`/findings?gene=${dossier.gene}`}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-line-strong bg-surface px-4 text-sm font-semibold text-ink hover:border-accent"
        >
          <DownloadSimple aria-hidden="true" size={17} />
          Prepare finding card
        </Link>
      </div>
    </>
  );
}
