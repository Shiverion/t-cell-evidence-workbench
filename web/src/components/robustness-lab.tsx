"use client";

import { ArrowCounterClockwise, Info } from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import { Metric, StatusBadge } from "@/components/ui";
import { conditionLabel, formatScore } from "@/lib/format";
import { CONDITIONS, type CandidateRow, type Condition } from "@/lib/types";

type Weights = {
  downstream: number;
  donor: number;
  guide: number;
};

type ScenarioRow = {
  row: CandidateRow;
  scenarioScore: number;
  scenarioRank: number;
  rankDelta: number;
};

const defaultWeights: Weights = {
  downstream: 1,
  donor: 1,
  guide: 1,
};

function calculateScore(row: CandidateRow, weights: Weights) {
  const totalWeight = weights.downstream + weights.donor + weights.guide;
  return Math.exp(
    (weights.downstream * Math.log(row.nDownstreamPercentile) +
      weights.donor * Math.log(row.crossdonorMinPercentile) +
      weights.guide * Math.log(row.crossguidePercentile)) /
      totalWeight,
  );
}

function rankScenario(rows: CandidateRow[], weights: Weights): ScenarioRow[] {
  const scored = rows
    .map((row) => ({ row, scenarioScore: calculateScore(row, weights) }))
    .sort(
      (left, right) =>
        right.scenarioScore - left.scenarioScore || left.row.gene.localeCompare(right.row.gene),
    );

  let previousScore: number | null = null;
  let previousRank = 0;
  return scored.map((item, index) => {
    const sameAsPrevious =
      previousScore != null && Math.abs(item.scenarioScore - previousScore) < 1e-12;
    const scenarioRank = sameAsPrevious ? previousRank : index + 1;
    previousScore = item.scenarioScore;
    previousRank = scenarioRank;
    return {
      ...item,
      scenarioRank,
      rankDelta: item.row.rankWithinCondition - scenarioRank,
    };
  });
}

function pearsonCorrelation(pairs: Array<[number, number]>) {
  if (pairs.length < 2) return 1;
  const meanLeft = pairs.reduce((sum, pair) => sum + pair[0], 0) / pairs.length;
  const meanRight = pairs.reduce((sum, pair) => sum + pair[1], 0) / pairs.length;
  let numerator = 0;
  let leftSquare = 0;
  let rightSquare = 0;
  pairs.forEach(([left, right]) => {
    const leftDelta = left - meanLeft;
    const rightDelta = right - meanRight;
    numerator += leftDelta * rightDelta;
    leftSquare += leftDelta ** 2;
    rightSquare += rightDelta ** 2;
  });
  const denominator = Math.sqrt(leftSquare * rightSquare);
  return denominator === 0 ? 1 : numerator / denominator;
}

function RankDelta({ value }: { value: number }) {
  if (value === 0) return <span className="text-ink-faint">—</span>;
  return (
    <span className={value > 0 ? "text-success" : "text-danger"}>
      {value > 0 ? `+${value}` : value}
    </span>
  );
}

export function RobustnessLab({ candidates }: { candidates: CandidateRow[] }) {
  const [condition, setCondition] = useState<Condition>("Rest");
  const [weights, setWeights] = useState<Weights>(defaultWeights);
  const conditionRows = useMemo(
    () => candidates.filter((row) => row.cultureCondition === condition),
    [candidates, condition],
  );
  const scenario = useMemo(
    () => rankScenario(conditionRows, weights),
    [conditionRows, weights],
  );
  const rankAgreement = useMemo(
    () =>
      pearsonCorrelation(
        scenario.map((item) => [item.row.rankWithinCondition, item.scenarioRank]),
      ),
    [scenario],
  );
  const baselineTopTen = useMemo(
    () =>
      new Set(
        conditionRows
          .filter((row) => row.rankWithinCondition <= 10)
          .map((row) => row.gene),
      ),
    [conditionRows],
  );
  const topTenOverlap = scenario
    .slice(0, 10)
    .filter((item) => baselineTopTen.has(item.row.gene)).length;
  const largestMoverCandidate = [...scenario].sort(
    (left, right) => Math.abs(right.rankDelta) - Math.abs(left.rankDelta),
  )[0];
  const largestMover =
    largestMoverCandidate && Math.abs(largestMoverCandidate.rankDelta) > 0
      ? largestMoverCandidate
      : null;
  const changed =
    weights.downstream !== 1 || weights.donor !== 1 || weights.guide !== 1;

  function updateWeight(key: keyof Weights, value: number) {
    setWeights((current) => ({ ...current, [key]: value }));
  }

  return (
    <>
      <section className="grid gap-7 xl:grid-cols-[20rem_minmax(0,1fr)]">
        <aside className="paper-surface border border-line bg-surface p-5">
          <div className="flex items-start justify-between gap-4 border-b border-line pb-4">
            <div>
              <p className="text-sm font-semibold text-ink">Scenario controls</p>
              <p className="mt-1 text-xs leading-5 text-ink-soft">Weighted geometric mean</p>
            </div>
            <StatusBadge tone="warning">Exploratory</StatusBadge>
          </div>

          <fieldset className="mt-5">
            <legend className="mb-2 text-xs font-medium text-ink-soft">Condition</legend>
            <div className="grid grid-cols-3 overflow-hidden rounded-lg border border-line-strong">
              {CONDITIONS.map((value) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={condition === value}
                  onClick={() => setCondition(value)}
                  className={`min-h-10 border-r border-line px-2 text-xs font-medium last:border-0 ${
                    condition === value
                      ? "bg-ink text-canvas"
                      : "bg-canvas text-ink-soft hover:bg-surface-strong"
                  }`}
                >
                  {value === "Stim8hr" ? "8 h" : value === "Stim48hr" ? "48 h" : "Rest"}
                </button>
              ))}
            </div>
          </fieldset>

          <div className="mt-6 space-y-6">
            {[
              {
                key: "downstream" as const,
                label: "Downstream percentile",
                description: "Power-sensitive source discovery count",
              },
              {
                key: "donor" as const,
                label: "Donor percentile",
                description: "Minimum source donor concordance",
              },
              {
                key: "guide" as const,
                label: "Guide percentile",
                description: "Source guide concordance",
              },
            ].map((control) => (
              <label key={control.key} className="block">
                <span className="flex items-baseline justify-between gap-3">
                  <span className="text-xs font-semibold text-ink">{control.label}</span>
                  <span className="numeric font-mono text-xs text-accent-dark">
                    {weights[control.key].toFixed(2)}×
                  </span>
                </span>
                <span className="mt-1 block text-[0.68rem] leading-5 text-ink-faint">
                  {control.description}
                </span>
                <input
                  type="range"
                  min="0.25"
                  max="2"
                  step="0.25"
                  value={weights[control.key]}
                  onChange={(event) =>
                    updateWeight(control.key, Number(event.target.value))
                  }
                  className="mt-2 h-5 w-full accent-[var(--accent)]"
                />
              </label>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setWeights(defaultWeights)}
            disabled={!changed}
            className="mt-7 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-line-strong bg-canvas px-4 text-sm font-semibold text-ink disabled:opacity-40"
          >
            <ArrowCounterClockwise aria-hidden="true" size={16} />
            Restore registered weights
          </button>
        </aside>

        <div>
          <div className="flex flex-col justify-between gap-4 border-b border-line pb-5 sm:flex-row sm:items-end">
            <div>
              <p className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-accent">
                {conditionLabel[condition]}
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-ink">
                {changed ? "Exploratory ranking" : "Registered ranking reproduced"}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-soft">
                Positive rank deltas move upward relative to the pinned default score.
              </p>
            </div>
            <StatusBadge tone={changed ? "warning" : "success"}>
              {changed ? "Weights modified" : "Default weights"}
            </StatusBadge>
          </div>

          <div className="grid divide-y divide-line border-b border-line sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            <div className="sm:pr-6">
              <Metric
                label="Rank agreement"
                value={formatScore(rankAgreement)}
                detail="Pearson correlation of full ranks"
              />
            </div>
            <div className="sm:px-6">
              <Metric
                label="Top-10 overlap"
                value={`${topTenOverlap} / 10`}
                detail="Genes retained from registered top 10"
              />
            </div>
            <div className="sm:pl-6">
              <Metric
                label="Largest mover"
                value={largestMover?.row.gene ?? "None"}
                detail={
                  largestMover ? (
                    <>
                      Rank change <RankDelta value={largestMover.rankDelta} />
                    </>
                  ) : (
                    "No rank changes"
                  )
                }
              />
            </div>
          </div>

          <div className="mt-6 overflow-x-auto border-y border-line bg-surface/50">
            <table className="w-full min-w-[700px] border-collapse text-left">
              <thead>
                <tr className="border-b border-line font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint">
                  <th className="px-3 py-3 font-medium">Gene</th>
                  <th className="px-3 py-3 text-right font-medium">Registered rank</th>
                  <th className="px-3 py-3 text-right font-medium">Scenario rank</th>
                  <th className="px-3 py-3 text-right font-medium">Change</th>
                  <th className="px-3 py-3 text-right font-medium">Scenario score</th>
                </tr>
              </thead>
              <tbody>
                {scenario.slice(0, 15).map((item) => (
                  <tr
                    key={item.row.gene}
                    className="border-b border-line/75 text-sm last:border-0"
                  >
                    <td className="px-3 py-3 font-semibold text-ink">{item.row.gene}</td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink-soft">
                      #{item.row.rankWithinCondition}
                    </td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs font-semibold text-ink">
                      #{item.scenarioRank}
                    </td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs font-semibold">
                      <RankDelta value={item.rankDelta} />
                    </td>
                    <td className="numeric px-3 py-3 text-right font-mono text-xs text-ink">
                      {formatScore(item.scenarioScore)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mt-9 flex items-start gap-3 border border-warning/35 bg-warning/10 p-5">
        <Info aria-hidden="true" size={20} className="mt-0.5 shrink-0 text-warning" />
        <div>
          <p className="text-sm font-semibold text-ink">Exploration does not change the contract</p>
          <p className="mt-1 max-w-4xl text-sm leading-6 text-ink-soft">
            This lab only reweights the three existing within-condition percentiles among rows
            that already passed every gate. It does not recompute source statistics, change
            eligibility, or create a new registered result.
          </p>
        </div>
      </section>
    </>
  );
}
