"use client";

import {
  CaretDown,
  CaretUp,
  MagnifyingGlass,
  Minus,
} from "@phosphor-icons/react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import Link from "next/link";
import { useMemo, useState } from "react";

import { EmptyState, StatusBadge } from "@/components/ui";
import { conditionLabel, formatInteger, formatScore } from "@/lib/format";
import { CONDITIONS, type CandidateRow, type Condition } from "@/lib/types";

const columnHelper = createColumnHelper<CandidateRow>();

export function CandidateExplorer({
  rows,
  crossConditionGenes,
}: {
  rows: CandidateRow[];
  crossConditionGenes: string[];
}) {
  const [query, setQuery] = useState("");
  const [condition, setCondition] = useState<Condition | "All">("All");
  const [minimumScore, setMinimumScore] = useState(0);
  const [onlyCrossCondition, setOnlyCrossCondition] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "priorityScore", desc: true },
  ]);
  const [visibleRows, setVisibleRows] = useState(30);
  const crossConditionSet = useMemo(
    () => new Set(crossConditionGenes),
    [crossConditionGenes],
  );

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toUpperCase();
    return rows.filter(
      (row) =>
        (!normalizedQuery || row.gene.includes(normalizedQuery)) &&
        (condition === "All" || row.cultureCondition === condition) &&
        row.priorityScore >= minimumScore &&
        (!onlyCrossCondition || crossConditionSet.has(row.gene)),
    );
  }, [condition, crossConditionSet, minimumScore, onlyCrossCondition, query, rows]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("gene", {
        header: "Gene",
        cell: (info) => (
          <div>
            <Link
              href={`/genes/${info.getValue()}`}
              className="font-semibold text-ink hover:text-accent-dark"
            >
              {info.getValue()}
            </Link>
            {crossConditionSet.has(info.getValue()) ? (
              <span className="ml-2 hidden align-middle sm:inline-flex">
                <StatusBadge tone="accent">3 conditions</StatusBadge>
              </span>
            ) : null}
          </div>
        ),
      }),
      columnHelper.accessor("cultureCondition", {
        header: "Condition",
        cell: (info) => (
          <span className="text-xs text-ink-soft">{conditionLabel[info.getValue()]}</span>
        ),
      }),
      columnHelper.accessor("rankWithinCondition", {
        header: "Rank",
        cell: (info) => (
          <span className="numeric font-mono text-xs text-ink">#{info.getValue()}</span>
        ),
      }),
      columnHelper.accessor("priorityScore", {
        header: "Priority score",
        cell: (info) => (
          <span className="numeric font-mono text-xs font-semibold text-ink">
            {formatScore(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("nDownstream", {
        header: "Downstream",
        cell: (info) => (
          <span className="numeric font-mono text-xs text-ink-soft">
            {formatInteger(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("crossdonorMin", {
        header: "Donor min",
        cell: (info) => (
          <span className="numeric font-mono text-xs text-ink-soft">
            {formatScore(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("crossguide", {
        header: "Guide",
        cell: (info) => (
          <span className="numeric font-mono text-xs text-ink-soft">
            {formatScore(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor("nCellsTarget", {
        header: "Targeted cells",
        cell: (info) => (
          <span className="numeric font-mono text-xs text-ink-soft">
            {formatInteger(info.getValue())}
          </span>
        ),
      }),
    ],
    [crossConditionSet],
  );

  // TanStack Table intentionally exposes stateful methods that React Compiler does not memoize.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  function resetFilters() {
    setQuery("");
    setCondition("All");
    setMinimumScore(0);
    setOnlyCrossCondition(false);
    setVisibleRows(30);
  }

  const renderedRows = table.getRowModel().rows.slice(0, visibleRows);

  return (
    <div
      id="review-candidate"
      data-review-target="candidate"
      tabIndex={-1}
      role="region"
      aria-label="Candidate exploration workspace"
      className="scroll-mt-24 outline-none"
    >
      <div className="paper-surface border border-line bg-surface p-4 sm:p-5">
        <div className="grid gap-4 xl:grid-cols-[minmax(16rem,1.4fr)_minmax(16rem,1fr)_minmax(12rem,0.75fr)_auto] xl:items-end">
          <label className="block">
            <span className="mb-2 block text-xs font-medium text-ink-soft">Gene search</span>
            <span className="flex min-h-11 items-center gap-2 rounded-lg border border-line-strong bg-canvas px-3 focus-within:border-accent">
              <MagnifyingGlass aria-hidden="true" size={17} className="text-ink-faint" />
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setVisibleRows(30);
                }}
                placeholder="SETDB1, ARNT, AHR…"
                className="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-faint"
              />
              {query ? (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  aria-label="Clear gene search"
                  className="text-ink-faint hover:text-ink"
                >
                  <Minus size={15} />
                </button>
              ) : null}
            </span>
          </label>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-ink-soft">Condition</legend>
            <div className="flex min-h-11 overflow-hidden rounded-lg border border-line-strong bg-canvas">
              {(["All", ...CONDITIONS] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={condition === value}
                  onClick={() => {
                    setCondition(value);
                    setVisibleRows(30);
                  }}
                  className={`flex-1 border-r border-line px-2 text-xs font-medium last:border-0 ${
                    condition === value
                      ? "bg-ink text-canvas"
                      : "text-ink-soft hover:bg-surface-strong"
                  }`}
                >
                  {value === "All"
                    ? "All"
                    : value === "Stim8hr"
                      ? "8 h"
                      : value === "Stim48hr"
                        ? "48 h"
                        : "Rest"}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="block">
            <span className="mb-2 flex justify-between text-xs font-medium text-ink-soft">
              <span>Minimum score</span>
              <span className="numeric font-mono text-ink">{minimumScore.toFixed(2)}</span>
            </span>
            <input
              type="range"
              min="0"
              max="0.95"
              step="0.05"
              value={minimumScore}
              onChange={(event) => {
                setMinimumScore(Number(event.target.value));
                setVisibleRows(30);
              }}
              className="h-11 w-full accent-[var(--accent)]"
            />
          </label>

          <label className="flex min-h-11 cursor-pointer items-center gap-2 rounded-lg border border-line-strong bg-canvas px-3 text-xs font-medium text-ink-soft">
            <input
              type="checkbox"
              checked={onlyCrossCondition}
              onChange={(event) => {
                setOnlyCrossCondition(event.target.checked);
                setVisibleRows(30);
              }}
              className="size-4 accent-[var(--accent)]"
            />
            All 3 conditions
          </label>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-soft">
          <span className="numeric font-mono font-semibold text-ink">
            {formatInteger(filteredRows.length)}
          </span>{" "}
          eligible perturbation-condition rows
        </p>
        <button
          type="button"
          onClick={resetFilters}
          className="text-xs font-semibold text-accent-dark hover:text-ink"
        >
          Reset filters
        </button>
      </div>

      {renderedRows.length ? (
        <>
          <div className="mt-3 overflow-x-auto border-y border-line bg-surface/55">
            <table className="w-full min-w-[850px] border-collapse text-left">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id} className="border-b border-line">
                    {headerGroup.headers.map((header) => {
                      const sortingDirection = header.column.getIsSorted();
                      return (
                        <th
                          key={header.id}
                          scope="col"
                          aria-sort={
                            sortingDirection === "asc"
                              ? "ascending"
                              : sortingDirection === "desc"
                                ? "descending"
                                : undefined
                          }
                          className="px-3 py-3 font-mono text-[0.66rem] uppercase tracking-[0.08em] text-ink-faint"
                        >
                          {header.isPlaceholder ? null : (
                            <button
                              type="button"
                              onClick={header.column.getToggleSortingHandler()}
                              disabled={!header.column.getCanSort()}
                              className="inline-flex items-center gap-1.5 text-left hover:text-ink"
                            >
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext(),
                              )}
                              {{
                                asc: <CaretUp aria-hidden="true" size={11} />,
                                desc: <CaretDown aria-hidden="true" size={11} />,
                              }[sortingDirection as string] ?? null}
                            </button>
                          )}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>
              <tbody>
                {renderedRows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-line/75 last:border-0 hover:bg-accent-soft/35"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="whitespace-nowrap px-3 py-3">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visibleRows < table.getRowModel().rows.length ? (
            <div className="mt-5 flex justify-center">
              <button
                type="button"
                onClick={() => setVisibleRows((current) => current + 30)}
                className="min-h-10 rounded-lg border border-line-strong bg-surface px-5 text-sm font-semibold text-ink hover:border-accent"
              >
                Show 30 more
              </button>
            </div>
          ) : null}
        </>
      ) : (
        <div className="mt-5">
          <EmptyState
            title="No candidates match these filters"
            description="Reduce the minimum score, broaden the condition, or clear the gene query."
          />
        </div>
      )}
    </div>
  );
}
