import { MagnifyingGlass } from "@phosphor-icons/react/ssr";

import { PrimaryLink, SecondaryLink } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="grid min-h-[65dvh] place-items-center">
      <div className="max-w-xl text-center">
        <span className="mx-auto grid size-12 place-items-center rounded-xl bg-surface-strong text-accent">
          <MagnifyingGlass aria-hidden="true" size={23} />
        </span>
        <p className="mt-6 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-accent">
          No eligible dossier
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-ink">
          This candidate is not in the eligible result table.
        </h1>
        <p className="mt-4 text-sm leading-6 text-ink-soft">
          It may have failed a registered source-QC gate, be absent from the source table, or use a
          different identifier.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <PrimaryLink href="/explore">Search candidates</PrimaryLink>
          <SecondaryLink href="/">Return to overview</SecondaryLink>
        </div>
      </div>
    </div>
  );
}
