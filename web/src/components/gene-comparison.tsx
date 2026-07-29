"use client";

import { Minus, Plus } from "@phosphor-icons/react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { EmptyState, StatusBadge } from "@/components/ui";
import { conditionLabel, formatInteger, formatScore } from "@/lib/format";
import { CONDITIONS, type CandidateRow } from "@/lib/types";

export function GeneComparison({
  candidates,
  geneNames,
  defaultGenes,
}: {
  candidates: CandidateRow[];
  geneNames: string[];
  defaultGenes: string[];
}) {
  const [selectedGenes, setSelectedGenes] = useState(defaultGenes);
  const [pendingGene, setPendingGene] = useState(
    geneNames.find((gene) => !defaultGenes.includes(gene)) ?? "",
  );

  const profiles = useMemo(
    () =>
      selectedGenes.map((gene) => ({
        gene,
        rows: candidates
          .filter((row) => row.gene === gene)
          .sort(
            (left, right) =>
              CONDITIONS.indexOf(left.cultureCondition) -
              CONDITIONS.indexOf(right.cultureCondition),
          ),
      })),
    [candidates, selectedGenes],
  );

  function addGene() {
    if (!pendingGene || selectedGenes.includes(pendingGene) || selectedGenes.length >= 5) return;
    const next = [...selectedGenes, pendingGene];
    setSelectedGenes(next);
    setPendingGene(geneNames.find((gene) => !next.includes(gene)) ?? "");
  }

  function removeGene(gene: string) {
    setSelectedGenes((current) => current.filter((value) => value !== gene));
  }

  return (
    <>
      <div className="paper-surface border border-line bg-surface p-4 sm:p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
          <label className="block min-w-0 flex-1">
            <span className="mb-2 block text-xs font-medium text-ink-soft">
              Add an eligible gene
            </span>
            <div className="flex gap-2">
              <select
                value={pendingGene}
                onChange={(event) => setPendingGene(event.target.value)}
                className="min-h-11 min-w-0 flex-1 rounded-lg border border-line-strong bg-canvas px-3 text-sm text-ink outline-none focus:border-accent"
              >
                {geneNames
                  .filter((gene) => !selectedGenes.includes(gene))
                  .map((gene) => (
                    <option key={gene} value={gene}>
                      {gene}
                    </option>
                  ))}
              </select>
              <button
                type="button"
                onClick={addGene}
                disabled={selectedGenes.length >= 5 || !pendingGene}
                className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-canvas disabled:cursor-not-allowed disabled:opacity-35"
              >
                <Plus aria-hidden="true" size={16} weight="bold" />
                Add
              </button>
            </div>
          </label>
          <p className="max-w-sm text-xs leading-5 text-ink-soft">
            Compare up to five genes. Values remain condition-relative and should not be read as
            formal interaction estimates.
          </p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
          {selectedGenes.map((gene) => (
            <span
              key={gene}
              className="inline-flex min-h-9 items-center gap-2 rounded-full border border-accent/25 bg-accent-soft px-3 text-xs font-semibold text-accent-dark"
            >
              {gene}
              <button
                type="button"
                onClick={() => removeGene(gene)}
                aria-label={`Remove ${gene} from comparison`}
                className="text-accent-dark/65 hover:text-ink"
              >
                <Minus size={13} weight="bold" />
              </button>
            </span>
          ))}
          <span className="ml-auto self-center font-mono text-[0.68rem] text-ink-faint">
            {selectedGenes.length} / 5 selected
          </span>
        </div>
      </div>

      {profiles.length ? (
        <>
          <section className="mt-10">
            <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <h2 className="text-xl font-semibold tracking-[-0.03em] text-ink">
                  Condition score profiles
                </h2>
                <p className="mt-1 text-sm leading-6 text-ink-soft">
                  Aligned scales make weak and missing conditions visible.
                </p>
              </div>
              <StatusBadge tone="neutral">Registered scores</StatusBadge>
            </div>
            <div className="divide-y divide-line border-y border-line">
              {profiles.map((profile) => (
                <div
                  key={profile.gene}
                  className="grid gap-5 py-5 md:grid-cols-[8rem_minmax(0,1fr)_5rem] md:items-center"
                >
                  <div>
                    <Link
                      href={`/genes/${profile.gene}`}
                      className="font-semibold text-ink hover:text-accent-dark"
                    >
                      {profile.gene}
                    </Link>
                    <p className="mt-1 text-xs text-ink-faint">
                      {profile.rows.length} eligible conditions
                    </p>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-3">
                    {CONDITIONS.map((condition) => {
                      const row = profile.rows.find(
                        (candidate) => candidate.cultureCondition === condition,
                      );
                      return (
                        <div key={condition}>
                          <div className="mb-1.5 flex items-baseline justify-between gap-2">
                            <span className="text-[0.68rem] text-ink-soft">
                              {conditionLabel[condition]}
                            </span>
                            <span className="numeric font-mono text-[0.68rem] text-ink">
                              {row ? formatScore(row.priorityScore) : "—"}
                            </span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-surface-strong">
                            {row ? (
                              <div
                                className="h-full rounded-full bg-accent"
                                style={{ width: `${row.priorityScore * 100}%` }}
                              />
                            ) : (
                              <div className="h-full w-full border border-dashed border-line-strong" />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="text-left md:text-right">
                    <p className="font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint">
                      Best rank
                    </p>
                    <p className="numeric mt-1 font-mono text-sm font-semibold text-ink">
                      #{Math.min(...profile.rows.map((row) => row.rankWithinCondition))}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-10">
            <div className="mb-5">
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-ink">
                Component comparison
              </h2>
              <p className="mt-1 text-sm leading-6 text-ink-soft">
                Raw source values are shown alongside the heuristic score.
              </p>
            </div>
            <div className="overflow-x-auto border-y border-line bg-surface/50">
              <table className="w-full min-w-[920px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-line font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint">
                    <th className="px-3 py-3 font-medium">Gene</th>
                    <th className="px-3 py-3 font-medium">Condition</th>
                    <th className="px-3 py-3 text-right font-medium">Rank</th>
                    <th className="px-3 py-3 text-right font-medium">Score</th>
                    <th className="px-3 py-3 text-right font-medium">Downstream</th>
                    <th className="px-3 py-3 text-right font-medium">Donor min</th>
                    <th className="px-3 py-3 text-right font-medium">Guide</th>
                    <th className="px-3 py-3 text-right font-medium">Cells</th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.flatMap((profile) =>
                    profile.rows.map((row) => (
                      <tr
                        key={`${profile.gene}-${row.cultureCondition}`}
                        className="border-b border-line/75 text-sm last:border-0"
                      >
                        <td className="px-3 py-3 font-semibold text-ink">{profile.gene}</td>
                        <td className="px-3 py-3 text-xs text-ink-soft">
                          {conditionLabel[row.cultureCondition]}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink">
                          #{row.rankWithinCondition}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs font-semibold text-ink">
                          {formatScore(row.priorityScore)}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                          {formatInteger(row.nDownstream)}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                          {formatScore(row.crossdonorMin)}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                          {formatScore(row.crossguide)}
                        </td>
                        <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                          {formatInteger(row.nCellsTarget)}
                        </td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <div className="mt-6">
          <EmptyState
            title="No genes selected"
            description="Add at least one eligible gene to build a registered comparison."
          />
        </div>
      )}
    </>
  );
}
