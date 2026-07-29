import { conditionLabel, formatInteger, stageLabel } from "@/lib/format";
import { CONDITIONS, type FunnelRow } from "@/lib/types";

export function FunnelChart({ rows }: { rows: FunnelRow[] }) {
  return (
    <div className="divide-y divide-line border-y border-line">
      {CONDITIONS.map((condition) => {
        const conditionRows = rows
          .filter((row) => row.cultureCondition === condition)
          .sort((left, right) => left.stageOrder - right.stageOrder);
        const startingRows = conditionRows.at(0)?.nRows ?? 1;

        return (
          <section key={condition} className="py-5">
            <div className="mb-4 flex items-baseline justify-between gap-4">
              <h3 className="text-sm font-semibold text-ink">{conditionLabel[condition]}</h3>
              <span className="numeric font-mono text-xs text-ink-faint">
                {formatInteger(conditionRows.at(-1)?.nRows ?? 0)} pass
              </span>
            </div>
            <div className="space-y-2.5">
              {conditionRows.map((row) => (
                <div key={row.stage} className="grid grid-cols-[minmax(7.5rem,1fr)_4.5rem] gap-3">
                  <div className="min-w-0">
                    <div className="mb-1 flex items-center justify-between gap-3">
                      <span className="truncate text-[0.7rem] text-ink-soft">
                        {stageLabel[row.stage] ?? row.stage}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-surface-strong">
                      <div
                        className="h-full rounded-full bg-accent"
                        style={{ width: `${Math.max((row.nRows / startingRows) * 100, 1.5)}%` }}
                      />
                    </div>
                  </div>
                  <span className="numeric pt-3 font-mono text-[0.7rem] text-ink-faint">
                    {formatInteger(row.nRows)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
