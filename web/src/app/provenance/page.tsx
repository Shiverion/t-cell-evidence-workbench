import {
  ArrowSquareOut,
  CheckCircle,
  FileText,
  Fingerprint,
} from "@phosphor-icons/react/ssr";
import type { Metadata } from "next";

import {
  Metric,
  PageHeader,
  SectionHeader,
  StatusBadge,
} from "@/components/ui";
import {
  formatBytes,
  formatInteger,
  sentenceCase,
} from "@/lib/format";
import {
  getBundleFingerprint,
  getManifest,
  getRunSummary,
} from "@/lib/data";

export const metadata: Metadata = {
  title: "Provenance",
};

export default async function ProvenancePage() {
  const [manifest, runSummary] = await Promise.all([getManifest(), getRunSummary()]);
  const bundleFingerprint = getBundleFingerprint();
  const generatedAt = new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(manifest.generatedAtUtc));

  return (
    <>
      <PageHeader
        eyebrow="Provenance"
        title="Every displayed result points back to a pinned run."
        description="Inspect source URLs, file hashes, the exact hard-gate contract, package versions, and generated artifacts. Local filesystem paths are intentionally not exposed."
        action={
          <StatusBadge tone="success">
            <CheckCircle aria-hidden="true" size={12} weight="fill" className="mr-1" />
            {runSummary.status} · bundle {bundleFingerprint.slice(0, 8)}
          </StatusBadge>
        }
      />

      <section className="grid gap-px border-b border-line bg-line sm:grid-cols-2 xl:grid-cols-4 [&>*]:bg-canvas">
        <div className="sm:pr-6">
          <Metric label="Workflow" value="CD4 triage" detail={manifest.workflow} />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Pinned source commit"
            value={manifest.pinnedCommit.slice(0, 8)}
            detail="Immutable Git revision"
          />
        </div>
        <div className="sm:px-6">
          <Metric
            label="Source artifacts"
            value={formatInteger(manifest.sourceFiles.length)}
            detail="Byte size and SHA-256 recorded"
          />
        </div>
        <div className="sm:pl-6">
          <Metric
            label="Generated artifacts"
            value={formatInteger(manifest.artifacts.length)}
            detail={`Manifest generated ${generatedAt} UTC`}
          />
        </div>
      </section>

      <section className="mt-12 grid gap-10 xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
        <div>
          <SectionHeader
            title="Pinned source files"
            description="URLs are safe to open; SHA-256 fingerprints identify the exact downloaded content."
          />
          <div className="divide-y divide-line border-y border-line">
            {manifest.sourceFiles.map((source) => (
              <article key={source.key} className="py-5">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText aria-hidden="true" size={18} className="text-accent" />
                      <h3 className="font-semibold text-ink">{sentenceCase(source.key)}</h3>
                    </div>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-flex max-w-full items-center gap-1.5 truncate text-xs text-accent-dark hover:text-ink"
                    >
                      {new URL(source.url).hostname}
                      <ArrowSquareOut aria-hidden="true" size={13} />
                    </a>
                  </div>
                  <span className="numeric font-mono text-xs text-ink-faint">
                    {formatBytes(source.bytes)}
                  </span>
                </div>
                <div className="mt-4 flex items-start gap-2 rounded-lg bg-surface-strong/65 p-3">
                  <Fingerprint aria-hidden="true" size={16} className="mt-0.5 shrink-0 text-ink-faint" />
                  <code className="break-all font-mono text-[0.68rem] leading-5 text-ink-soft">
                    {source.sha256}
                  </code>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside>
          <SectionHeader
            title="Registered hard gates"
            description="These rules define eligibility before ranking."
          />
          <dl className="divide-y divide-line border-y border-line">
            {Object.entries(manifest.analysisContract.hardGates).map(([key, value]) => (
              <div key={key} className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 py-4">
                <dt className="text-xs text-ink-soft">{sentenceCase(key)}</dt>
                <dd className="numeric text-right font-mono text-xs font-semibold text-ink">
                  {String(value)}
                </dd>
              </div>
            ))}
          </dl>
          <div className="mt-5 border border-line bg-surface/55 p-5">
            <p className="text-xs font-semibold text-ink">Contract parameters</p>
            <dl className="mt-4 space-y-3 text-xs">
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Minimum targeted cells</dt>
                <dd className="font-mono text-ink">
                  {manifest.analysisContract.minCellsTarget}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Top rows per condition</dt>
                <dd className="font-mono text-ink">{manifest.analysisContract.topN}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Conditions</dt>
                <dd className="text-right font-mono text-ink">
                  {manifest.analysisContract.conditions.join(" · ")}
                </dd>
              </div>
            </dl>
            <div className="mt-5 border-t border-line pt-4">
              <p className="text-xs text-ink-soft">Analysis bundle SHA-256</p>
              <code className="mt-2 block break-all font-mono text-[0.66rem] leading-5 text-ink">
                {bundleFingerprint}
              </code>
            </div>
          </div>
        </aside>
      </section>

      <section className="mt-12 grid gap-10 xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
        <div>
          <SectionHeader
            title="Generated artifact ledger"
            description="Each file is captured with its relative output path, byte size, and fingerprint."
          />
          <div className="max-h-[34rem] overflow-y-auto border-y border-line">
            {manifest.artifacts.map((artifact) => (
              <details key={artifact.path} className="border-b border-line/75 last:border-0">
                <summary className="flex cursor-pointer items-center justify-between gap-5 px-2 py-3 text-xs hover:bg-accent-soft/30">
                  <span className="min-w-0 truncate font-mono text-ink">{artifact.path}</span>
                  <span className="numeric shrink-0 font-mono text-ink-faint">
                    {formatBytes(artifact.bytes)}
                  </span>
                </summary>
                <div className="bg-surface-strong/55 px-3 py-3">
                  <code className="break-all font-mono text-[0.66rem] leading-5 text-ink-soft">
                    SHA-256 {artifact.sha256}
                  </code>
                </div>
              </details>
            ))}
          </div>
        </div>

        <aside>
          <SectionHeader title="Runtime versions" description="Recorded by the Python workflow." />
          <dl className="divide-y divide-line border-y border-line">
            {Object.entries(manifest.packageVersions).map(([name, version]) => (
              <div key={name} className="flex justify-between gap-4 py-4 text-xs">
                <dt className="text-ink-soft">{name}</dt>
                <dd className="font-mono font-semibold text-ink">{version}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-6 border border-warning/35 bg-warning/10 p-5">
            <p className="text-sm font-semibold text-ink">What provenance does not prove</p>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              A passed schema audit confirms expected structure and traceability. It does not
              establish that the source biological or statistical model is correct.
            </p>
          </div>
        </aside>
      </section>
    </>
  );
}
