import { conditionLabel, formatInteger, formatScore } from "@/lib/format";
import type { CandidateRow } from "@/lib/types";

const components = [
  {
    key: "nDownstreamPercentile",
    label: "Downstream discoveries",
    value: (row: CandidateRow) => formatInteger(row.nDownstream),
  },
  {
    key: "crossdonorMinPercentile",
    label: "Minimum donor concordance",
    value: (row: CandidateRow) => formatScore(row.crossdonorMin),
  },
  {
    key: "crossguidePercentile",
    label: "Guide concordance",
    value: (row: CandidateRow) => formatScore(row.crossguide),
  },
] as const;

export function ScoreAnatomy({ rows }: { rows: CandidateRow[] }) {
  return (
    <div className="divide-y divide-line border-y border-line">
      {rows.map((row) => (
        <section key={row.cultureCondition} className="py-5">
          <div className="flex items-baseline justify-between gap-4">
            <h3 className="text-sm font-semibold text-ink">
              {conditionLabel[row.cultureCondition]}
            </h3>
            <span className="numeric font-mono text-xs font-semibold text-accent-dark">
              #{row.rankWithinCondition} · {formatScore(row.priorityScore)}
            </span>
          </div>
          <div className="mt-4 space-y-3">
            {components.map((component) => {
              const percentile = row[component.key];
              return (
                <div key={component.key} className="grid grid-cols-[minmax(9rem,1fr)_4rem] gap-3">
                  <div>
                    <div className="mb-1.5 flex items-baseline justify-between gap-3">
                      <span className="text-xs text-ink-soft">{component.label}</span>
                      <span className="numeric font-mono text-[0.68rem] text-ink-faint">
                        p{Math.round(percentile * 100)}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-surface-strong">
                      <div
                        className="h-full rounded-full bg-accent"
                        style={{ width: `${percentile * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="numeric pt-4 text-right font-mono text-[0.7rem] text-ink">
                    {component.value(row)}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
