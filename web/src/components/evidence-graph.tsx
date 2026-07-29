"use client";

import {
  ArrowLeft,
  ArrowRight,
  ArrowsCounterClockwise,
  ArrowsOutSimple,
  ChartLineUp,
  Check,
  CircleNotch,
  Columns,
  Database,
  MagnifyingGlass,
  Note,
  Rows,
  StackSimple,
  Target,
  TestTube,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  type OnSelectionChangeFunc,
} from "@xyflow/react";
import ELK, { type ElkNode } from "elkjs/lib/elk.bundled.js";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { conditionLabel, formatScore, formatSigned } from "@/lib/format";
import type { GeneDossier } from "@/lib/types";

import "@xyflow/react/dist/style.css";

type EvidenceKind =
  | "gene"
  | "result"
  | "summary"
  | "annotation"
  | "followup"
  | "gap"
  | "source";

type NodeDetails = {
  id: string;
  label: string;
  type: EvidenceKind;
  eyebrow: string;
  detail: string;
  metric: string;
};

type EvidenceNodeData = NodeDetails & {
  dimmed?: boolean;
  focused?: boolean;
  related?: boolean;
};

type EvidenceNode = Node<EvidenceNodeData, "evidence">;
type EvidenceEdgeData = {
  relation: string;
};
type EvidenceEdge = Edge<EvidenceEdgeData>;
type LayoutDirection = "RIGHT" | "DOWN";

const elk = new ELK();
const ELK_LAYOUT_TIMEOUT_MS = 1_500;
const LAYOUT_NODE_GAP = 42;
const LAYOUT_LAYER_GAP = 88;
const LAYOUT_PADDING = 32;

const nodeDimensions: Record<EvidenceKind, { width: number; height: number }> = {
  gene: { width: 174, height: 82 },
  result: { width: 202, height: 82 },
  summary: { width: 202, height: 82 },
  annotation: { width: 220, height: 82 },
  followup: { width: 202, height: 82 },
  gap: { width: 202, height: 82 },
  source: { width: 184, height: 82 },
};

function KindIcon({ type }: { type: EvidenceKind }) {
  const common = { size: 16, weight: "duotone" as const, "aria-hidden": true };

  switch (type) {
    case "gene":
      return <Target {...common} />;
    case "result":
      return <ChartLineUp {...common} />;
    case "summary":
      return <StackSimple {...common} />;
    case "annotation":
      return <Note {...common} />;
    case "followup":
      return <TestTube {...common} />;
    case "gap":
      return <WarningCircle {...common} />;
    case "source":
      return <Database {...common} />;
  }
}

function EvidenceNodeCard({ data, selected }: NodeProps<EvidenceNode>) {
  return (
    <article
      className={[
        "evidence-node",
        `evidence-node--${data.type}`,
        selected || data.focused ? "is-focused" : "",
        data.related ? "is-related" : "",
        data.dimmed ? "is-dimmed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={false}
        className="evidence-handle"
      />
      <div className="evidence-node__icon">
        <KindIcon type={data.type} />
      </div>
      <div className="min-w-0">
        <p className="evidence-node__eyebrow">{data.eyebrow}</p>
        <h3 className="evidence-node__label">{data.label}</h3>
        <p className="evidence-node__metric numeric">{data.metric}</p>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={false}
        className="evidence-handle"
      />
    </article>
  );
}

const nodeTypes = {
  evidence: EvidenceNodeCard,
};

function buildGraph(
  dossier: GeneDossier,
  showAnnotations: boolean,
  showSources: boolean,
): {
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
  details: Map<string, NodeDetails>;
} {
  const nodes: EvidenceNode[] = [];
  const edges: EvidenceEdge[] = [];
  const details = new Map<string, NodeDetails>();
  const geneId = `gene-${dossier.gene}`;

  function addNode(node: NodeDetails) {
    const dimensions = nodeDimensions[node.type];
    details.set(node.id, node);
    nodes.push({
      id: node.id,
      type: "evidence",
      position: { x: 0, y: 0 },
      data: node,
      width: dimensions.width,
      height: dimensions.height,
      style: dimensions,
      focusable: true,
      ariaLabel: `${node.label}. ${node.eyebrow}. ${node.metric}`,
    });
  }

  function addEdge(id: string, source: string, target: string, relation: string) {
    edges.push({
      id,
      source,
      target,
      type: "smoothstep",
      data: { relation },
      focusable: true,
      selectable: false,
    });
  }

  addNode({
    id: geneId,
    label: dossier.gene,
    type: "gene",
    eyebrow: "Perturbation target",
    detail: `${dossier.gene} is represented as a target gene, not as a validated mechanism or therapeutic target.`,
    metric: "Target gene",
  });

  dossier.conditionRows.forEach((row) => {
    const resultId = `result-${row.cultureCondition}`;
    addNode({
      id: resultId,
      label: conditionLabel[row.cultureCondition],
      type: "result",
      eyebrow: "Registered result",
      detail: `Rank #${row.rankWithinCondition}; priority score ${formatScore(row.priorityScore)}. Passed all six registered source-QC gates.`,
      metric: `#${row.rankWithinCondition} · score ${formatScore(row.priorityScore)}`,
    });
    addEdge(
      `gene-result-${row.cultureCondition}`,
      geneId,
      resultId,
      "has result",
    );
  });

  if (dossier.crossCondition) {
    const summaryId = "cross-condition-summary";
    addNode({
      id: summaryId,
      label: `Cross-condition #${dossier.crossCondition.crossConditionRank}`,
      type: "summary",
      eyebrow: "Maximin summary",
      detail: `Minimum condition score ${formatScore(dossier.crossCondition.minPriorityScore)}; ${conditionLabel[dossier.crossCondition.worstCondition]} is the lowest-scoring condition. This is not an interaction test.`,
      metric: `min score ${formatScore(dossier.crossCondition.minPriorityScore)}`,
    });
    addEdge("gene-cross-summary", geneId, summaryId, "has summary");
    dossier.conditionRows.forEach((row) => {
      addEdge(
        `summary-result-${row.cultureCondition}`,
        summaryId,
        `result-${row.cultureCondition}`,
        "derived from",
      );
    });
  }

  if (showAnnotations) {
    dossier.coefficients.forEach((coefficient, index) => {
      const annotationId = `annotation-${index}`;
      addNode({
        id: annotationId,
        label: `${coefficient.signature} · ${conditionLabel[coefficient.celltype]}`,
        type: "annotation",
        eyebrow: "Source annotation",
        detail: `Author-reported coefficient ${formatSigned(coefficient.coefficientMean, 4)} ± ${formatScore(coefficient.coefficientSem, 4)} SEM. This workflow did not refit the model.`,
        metric: `β ${formatSigned(coefficient.coefficientMean, 4)}`,
      });
      const matchingResult = dossier.conditionRows.find(
        (row) => row.cultureCondition === coefficient.celltype,
      );
      addEdge(
        `annotation-edge-${index}`,
        matchingResult ? `result-${matchingResult.cultureCondition}` : geneId,
        annotationId,
        "source annotation",
      );
    });
  }

  const followupId = dossier.validation ? "arrayed-followup" : "followup-gap";
  addNode(
    dossier.validation
      ? {
          id: followupId,
          label: "IL-10 / IL-21",
          type: "followup",
          eyebrow: "Arrayed follow-up",
          detail: `${dossier.validation.nDonors} observed donors. Deltas are percentage points relative to donor-matched NTC means; no confirmatory test was run.`,
          metric: `${dossier.validation.nDonors} donors`,
        }
      : {
          id: followupId,
          label: "No arrayed follow-up",
          type: "gap",
          eyebrow: "Evidence gap",
          detail:
            "This perturbation is absent from the selected author-provided IL-10/IL-21 follow-up table.",
          metric: "Not measured",
        },
  );
  addEdge(
    "gene-followup",
    geneId,
    followupId,
    dossier.validation ? "has follow-up" : "not measured",
  );

  if (showSources) {
    addNode({
      id: "source-de",
      label: "DE summary",
      type: "source",
      eyebrow: "Pinned source",
      detail:
        "The condition results use author-reported summary statistics from the pinned DE supplementary table.",
      metric: "Verified artifact",
    });
    dossier.conditionRows.forEach((row) => {
      addEdge(
        `result-source-${row.cultureCondition}`,
        `result-${row.cultureCondition}`,
        "source-de",
        "derived from",
      );
    });
  }

  return { nodes, edges, details };
}

function fallbackLayout(
  nodes: EvidenceNode[],
  edges: EvidenceEdge[],
  direction: LayoutDirection,
) {
  const horizontal = direction === "RIGHT";
  const depthById = new Map(nodes.map((node) => [node.id, 0]));
  const incomingById = new Map(nodes.map((node) => [node.id, 0]));
  const outgoingById = new Map(nodes.map((node) => [node.id, [] as string[]]));

  edges.forEach((edge) => {
    if (!incomingById.has(edge.target) || !outgoingById.has(edge.source)) return;
    incomingById.set(edge.target, (incomingById.get(edge.target) ?? 0) + 1);
    outgoingById.get(edge.source)?.push(edge.target);
  });

  const queue = nodes
    .filter((node) => incomingById.get(node.id) === 0)
    .map((node) => node.id);
  const processed = new Set<string>();

  while (queue.length > 0) {
    const sourceId = queue.shift();
    if (!sourceId) continue;
    processed.add(sourceId);

    (outgoingById.get(sourceId) ?? []).forEach((targetId) => {
      depthById.set(
        targetId,
        Math.max(
          depthById.get(targetId) ?? 0,
          (depthById.get(sourceId) ?? 0) + 1,
        ),
      );
      const remainingIncoming = (incomingById.get(targetId) ?? 1) - 1;
      incomingById.set(targetId, remainingIncoming);
      if (remainingIncoming === 0) queue.push(targetId);
    });
  }

  // Cyclic or malformed fragments cannot be topologically sorted. Keep them
  // visible in a final layer instead of leaving every node at the origin.
  const finalDepth =
    Math.max(0, ...[...depthById.entries()]
      .filter(([id]) => processed.has(id))
      .map(([, depth]) => depth)) + 1;
  nodes.forEach((node) => {
    if (!processed.has(node.id)) depthById.set(node.id, finalDepth);
  });

  const layers = new Map<number, EvidenceNode[]>();
  nodes.forEach((node) => {
    const depth = depthById.get(node.id) ?? 0;
    const layer = layers.get(depth) ?? [];
    layer.push(node);
    layers.set(depth, layer);
  });

  const orderedLayers = [...layers.entries()].sort(
    ([firstDepth], [secondDepth]) => firstDepth - secondDepth,
  );
  const layerCrossSizes = orderedLayers.map(([, layer]) =>
    layer.reduce((total, node, index) => {
      const dimensions = nodeDimensions[node.data.type];
      const crossSize = horizontal ? dimensions.height : dimensions.width;
      return total + crossSize + (index === 0 ? 0 : LAYOUT_NODE_GAP);
    }, 0),
  );
  const maxCrossSize = Math.max(0, ...layerCrossSizes);
  const positions = new Map<string, { x: number; y: number }>();
  let primaryOffset = LAYOUT_PADDING;

  orderedLayers.forEach(([, layer], layerIndex) => {
    const layerPrimarySize = Math.max(
      ...layer.map((node) => {
        const dimensions = nodeDimensions[node.data.type];
        return horizontal ? dimensions.width : dimensions.height;
      }),
    );
    let crossOffset =
      LAYOUT_PADDING + (maxCrossSize - layerCrossSizes[layerIndex]) / 2;

    layer.forEach((node) => {
      const dimensions = nodeDimensions[node.data.type];
      positions.set(
        node.id,
        horizontal
          ? { x: primaryOffset, y: crossOffset }
          : { x: crossOffset, y: primaryOffset },
      );
      crossOffset +=
        (horizontal ? dimensions.height : dimensions.width) + LAYOUT_NODE_GAP;
    });

    primaryOffset += layerPrimarySize + LAYOUT_LAYER_GAP;
  });

  return nodes.map((node) => ({
    ...node,
    position: positions.get(node.id) ?? {
      x: LAYOUT_PADDING,
      y: LAYOUT_PADDING,
    },
    sourcePosition: horizontal ? Position.Right : Position.Bottom,
    targetPosition: horizontal ? Position.Left : Position.Top,
  }));
}

async function elkLayoutWithTimeout(graph: ElkNode) {
  let timeoutId: number | undefined;

  try {
    return await Promise.race([
      elk.layout(graph),
      new Promise<never>((_, reject) => {
        timeoutId = window.setTimeout(() => {
          reject(new Error("ELK layout timed out."));
        }, ELK_LAYOUT_TIMEOUT_MS);
      }),
    ]);
  } finally {
    if (timeoutId !== undefined) window.clearTimeout(timeoutId);
  }
}

async function layoutGraph(
  nodes: EvidenceNode[],
  edges: EvidenceEdge[],
  direction: LayoutDirection,
) {
  const horizontal = direction === "RIGHT";
  const graph: ElkNode = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": direction,
      "elk.edgeRouting": "ORTHOGONAL",
      "elk.spacing.nodeNode": String(LAYOUT_NODE_GAP),
      "elk.layered.spacing.nodeNodeBetweenLayers": String(LAYOUT_LAYER_GAP),
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
      "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
      "elk.padding": `[top=${LAYOUT_PADDING},left=${LAYOUT_PADDING},bottom=${LAYOUT_PADDING},right=${LAYOUT_PADDING}]`,
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: nodeDimensions[node.data.type].width,
      height: nodeDimensions[node.data.type].height,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  if (typeof Worker !== "function" || typeof Blob !== "function") {
    return fallbackLayout(nodes, edges, direction);
  }

  try {
    const layout = await elkLayoutWithTimeout(graph);
    const positions = new Map(
      layout.children?.map((node) => [
        node.id,
        { x: node.x ?? 0, y: node.y ?? 0 },
      ]) ?? [],
    );

    return nodes.map((node) => ({
      ...node,
      position: positions.get(node.id) ?? { x: 0, y: 0 },
      sourcePosition: horizontal ? Position.Right : Position.Bottom,
      targetPosition: horizontal ? Position.Left : Position.Top,
    }));
  } catch {
    return fallbackLayout(nodes, edges, direction);
  }
}

function connectedIds(id: string | null, edges: EvidenceEdge[]) {
  if (!id) return new Set<string>();
  const ids = new Set([id]);
  edges.forEach((edge) => {
    if (edge.source === id) ids.add(edge.target);
    if (edge.target === id) ids.add(edge.source);
  });
  return ids;
}

function graphDuration() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 360;
}

function GraphWorkspace({ dossier }: { dossier: GeneDossier }) {
  const geneId = `gene-${dossier.gene}`;
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [showSources, setShowSources] = useState(true);
  const [showRelationLabels, setShowRelationLabels] = useState(false);
  const [direction, setDirection] = useState<LayoutDirection>("RIGHT");
  const [layoutRevision, setLayoutRevision] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [completedLayoutKey, setCompletedLayoutKey] = useState("");
  const [layoutError, setLayoutError] = useState<{
    key: string;
    message: string;
  } | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<EvidenceNode>([]);
  const [edges, setEdges] = useState<EvidenceEdge[]>([]);
  const { fitView } = useReactFlow<EvidenceNode, EvidenceEdge>();

  const graph = useMemo(
    () => buildGraph(dossier, showAnnotations, showSources),
    [dossier, showAnnotations, showSources],
  );
  const layoutKey = `${dossier.gene}:${showAnnotations}:${showSources}:${direction}:${layoutRevision}`;
  const layoutReady = completedLayoutKey === layoutKey;
  const activeLayoutError =
    layoutError?.key === layoutKey ? layoutError.message : null;
  const activeSelectedId =
    selectedId && graph.details.has(selectedId) ? selectedId : null;

  useEffect(() => {
    let cancelled = false;
    let fitFrame = 0;
    let secondFitFrame = 0;

    layoutGraph(graph.nodes, graph.edges, direction)
      .then((layoutedNodes) => {
        if (cancelled) return;
        setNodes(layoutedNodes);
        setEdges(graph.edges);
        setCompletedLayoutKey(layoutKey);
        setLayoutError(null);
        fitFrame = window.requestAnimationFrame(() => {
          secondFitFrame = window.requestAnimationFrame(() => {
            const compactViewport = window.innerWidth < 900;
            const initialNodes = compactViewport
              ? [...connectedIds(geneId, graph.edges)].map((id) => ({ id }))
              : undefined;
            void fitView({
              nodes: initialNodes,
              padding: compactViewport ? 0.42 : 0.17,
              minZoom: compactViewport ? 0.42 : 0.2,
              maxZoom: compactViewport ? 0.9 : 1,
              duration: graphDuration(),
            });
          });
        });
      })
      .catch(() => {
        if (cancelled) return;
        setLayoutError({
          key: layoutKey,
          message: "The automatic layout could not be calculated.",
        });
        setCompletedLayoutKey(layoutKey);
      });

    return () => {
      cancelled = true;
      window.cancelAnimationFrame(fitFrame);
      window.cancelAnimationFrame(secondFitFrame);
    };
  }, [
    direction,
    fitView,
    geneId,
    graph.edges,
    graph.nodes,
    layoutKey,
    layoutRevision,
    setNodes,
  ]);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const editing =
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.tagName === "SELECT" ||
        target?.isContentEditable;

      if (event.key === "/" && !editing) {
        event.preventDefault();
        searchRef.current?.focus();
      }

      if (event.key === "Escape" && !editing) {
        setSelectedId(null);
        setHoveredId(null);
      }
    }

    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const focusId = activeSelectedId ?? hoveredId;
  const neighborhood = useMemo(
    () => connectedIds(focusId, edges),
    [edges, focusId],
  );

  const displayNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        selected: node.id === activeSelectedId,
        data: {
          ...node.data,
          focused: node.id === focusId,
          related: Boolean(focusId && neighborhood.has(node.id)),
          dimmed: Boolean(focusId && !neighborhood.has(node.id)),
        },
      })),
    [activeSelectedId, focusId, neighborhood, nodes],
  );

  const displayEdges = useMemo(
    () =>
      edges.map((edge) => {
        const focused = Boolean(
          focusId &&
            (edge.source === focusId || edge.target === focusId),
        );
        const dimmed = Boolean(focusId && !focused);
        const stroke = focused
          ? "var(--graph-edge-active)"
          : dimmed
            ? "var(--graph-edge-dim)"
            : "var(--graph-edge)";

        return {
          ...edge,
          label:
            showRelationLabels || focused ? edge.data?.relation : undefined,
          className: focused ? "evidence-edge is-focused" : "evidence-edge",
          style: {
            stroke,
            strokeWidth: focused ? 2.2 : 1.25,
            opacity: dimmed ? 0.2 : 1,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 15,
            height: 15,
            color: stroke,
          },
          labelStyle: {
            fill: "var(--ink-soft)",
            fontSize: 10,
            fontWeight: 600,
          },
          labelBgStyle: {
            fill: "var(--surface)",
            fillOpacity: 0.96,
          },
          labelBgPadding: [6, 4] as [number, number],
          labelBgBorderRadius: 4,
        };
      }),
    [edges, focusId, showRelationLabels],
  );

  const inspectedId = activeSelectedId ?? geneId;
  const inspected =
    graph.details.get(inspectedId) ?? graph.details.values().next().value;

  const incoming = useMemo(
    () => edges.filter((edge) => edge.target === inspectedId),
    [edges, inspectedId],
  );
  const outgoing = useMemo(
    () => edges.filter((edge) => edge.source === inspectedId),
    [edges, inspectedId],
  );

  const searchResults = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase();
    if (!query) return [];
    return [...graph.details.values()]
      .filter((node) =>
        `${node.label} ${node.eyebrow} ${node.metric}`
          .toLocaleLowerCase()
          .includes(query),
      )
      .slice(0, 7);
  }, [graph.details, searchQuery]);

  const handleSelectionChange = useCallback<
    OnSelectionChangeFunc<EvidenceNode, EvidenceEdge>
  >(({ nodes: selectedNodes }) => {
    const nextSelectedId = selectedNodes.at(0)?.id;
    if (!nextSelectedId) return;

    setSelectedId((currentSelectedId) =>
      currentSelectedId === nextSelectedId ? currentSelectedId : nextSelectedId,
    );
  }, []);

  const focusNode = useCallback(
    (id: string, center = false) => {
      if (!graph.details.has(id)) return;
      setSelectedId(id);
      setHoveredId(null);
      if (center) {
        const ids = connectedIds(id, edges);
        void fitView({
          nodes: [...ids].map((nodeId) => ({ id: nodeId })),
          padding: 0.65,
          minZoom: 0.5,
          maxZoom: 1.15,
          duration: graphDuration(),
        });
      }
    },
    [edges, fitView, graph.details],
  );

  function submitSearch() {
    const first = searchResults[0];
    if (!first) return;
    setSearchQuery(first.label);
    focusNode(first.id, true);
  }

  function relationButton(edge: EvidenceEdge, incomingRelation: boolean) {
    const neighborId = incomingRelation ? edge.source : edge.target;
    const neighbor = graph.details.get(neighborId);
    if (!neighbor) return null;

    return (
      <button
        key={edge.id}
        type="button"
        onClick={() => focusNode(neighborId, true)}
        className="group flex min-h-11 w-full items-center gap-3 border-t border-line py-2 text-left first:border-t-0"
      >
        {incomingRelation ? (
          <ArrowLeft
            aria-hidden="true"
            size={14}
            className="shrink-0 text-ink-faint group-hover:text-accent"
          />
        ) : (
          <ArrowRight
            aria-hidden="true"
            size={14}
            className="shrink-0 text-ink-faint group-hover:text-accent"
          />
        )}
        <span className="min-w-0 flex-1">
          <span className="block truncate text-xs font-semibold text-ink">
            {neighbor.label}
          </span>
          <span className="mt-0.5 block text-[0.68rem] text-ink-faint">
            {edge.data?.relation}
          </span>
        </span>
      </button>
    );
  }

  return (
    <section className="paper-surface overflow-hidden border border-line bg-surface">
      <div className="border-b border-line px-4 py-4 sm:px-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold tracking-[-0.02em] text-ink">
                Interactive evidence graph
              </h2>
              <span className="border border-line bg-surface-strong px-2 py-1 font-mono text-[0.64rem] font-semibold uppercase tracking-[0.08em] text-ink-faint">
                {graph.nodes.length} nodes · {graph.edges.length} relations
              </span>
            </div>
            <p className="mt-1.5 max-w-2xl text-xs leading-5 text-ink-soft">
              Hover to preview a neighborhood. Select a card to lock focus, inspect
              its lineage, or drag it aside. Press / to search.
            </p>
          </div>
          <div
            className="inline-flex self-start rounded-lg border border-line bg-canvas p-1"
            role="group"
            aria-label="Graph layout direction"
          >
            {[
              { value: "RIGHT" as const, label: "Horizontal", icon: Columns },
              { value: "DOWN" as const, label: "Vertical", icon: Rows },
            ].map((option) => {
              const Icon = option.icon;
              return (
                <button
                  key={option.value}
                  type="button"
                  aria-label={`${option.label} graph layout`}
                  aria-pressed={direction === option.value}
                  onClick={() => setDirection(option.value)}
                  className={`inline-flex min-h-11 items-center gap-1.5 rounded-md px-2.5 text-xs font-semibold ${
                    direction === option.value
                      ? "bg-surface-strong text-accent-dark"
                      : "text-ink-faint hover:text-ink"
                  }`}
                >
                  <Icon aria-hidden="true" size={14} />
                  <span className="hidden sm:inline">{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-2 xl:flex-row xl:items-start">
          <form
            className="relative min-w-0 flex-1"
            role="search"
            aria-label="Find an evidence node"
            onSubmit={(event) => {
              event.preventDefault();
              submitSearch();
            }}
          >
            <MagnifyingGlass
              aria-hidden="true"
              size={16}
              className="pointer-events-none absolute left-3 top-3.5 text-ink-faint"
            />
            <input
              ref={searchRef}
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Find a result, annotation, source…"
              role="combobox"
              aria-autocomplete="list"
              aria-label="Search evidence nodes"
              aria-controls="evidence-search-results"
              aria-expanded={Boolean(searchQuery.trim() && searchResults.length)}
              className="min-h-11 w-full rounded-lg border border-line-strong bg-canvas pl-9 pr-12 text-xs text-ink outline-none placeholder:text-ink-faint focus:border-accent"
            />
            <kbd className="pointer-events-none absolute right-3 top-2.5 border border-line bg-surface-strong px-1.5 py-0.5 font-mono text-[0.65rem] text-ink-faint">
              /
            </kbd>
            {searchQuery.trim() ? (
              <div
                id="evidence-search-results"
                role="listbox"
                aria-label="Matching evidence nodes"
                className="absolute inset-x-0 top-[calc(100%+0.35rem)] z-30 max-h-72 overflow-y-auto border border-line-strong bg-surface p-1 shadow-2xl"
              >
                {searchResults.length ? (
                  searchResults.map((result) => (
                    <button
                      key={result.id}
                      type="button"
                      role="option"
                      aria-selected={activeSelectedId === result.id}
                      onClick={() => {
                        setSearchQuery(result.label);
                        focusNode(result.id, true);
                      }}
                      className="flex min-h-11 w-full items-center justify-between gap-3 rounded-md px-3 text-left hover:bg-surface-strong"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-xs font-semibold text-ink">
                          {result.label}
                        </span>
                        <span className="mt-0.5 block truncate text-[0.68rem] text-ink-faint">
                          {result.eyebrow}
                        </span>
                      </span>
                      <span className="shrink-0 font-mono text-[0.65rem] text-accent">
                        {result.metric}
                      </span>
                    </button>
                  ))
                ) : (
                  <p className="px-3 py-3 text-xs text-ink-soft">
                    No matching evidence node.
                  </p>
                )}
              </div>
            ) : null}
          </form>

          <div className="flex flex-wrap gap-2">
            {[
              {
                label: "Annotations",
                active: showAnnotations,
                toggle: () => setShowAnnotations((current) => !current),
              },
              {
                label: "Provenance",
                active: showSources,
                toggle: () => setShowSources((current) => !current),
              },
              {
                label: "Relation labels",
                active: showRelationLabels,
                toggle: () => setShowRelationLabels((current) => !current),
              },
            ].map((filter) => (
              <button
                key={filter.label}
                type="button"
                aria-pressed={filter.active}
                onClick={filter.toggle}
                className={`inline-flex min-h-11 items-center gap-1.5 rounded-lg border px-3 text-xs font-semibold ${
                  filter.active
                    ? "border-accent/35 bg-accent-soft text-accent-dark"
                    : "border-line bg-canvas text-ink-soft hover:border-line-strong hover:text-ink"
                }`}
              >
                {filter.active ? (
                  <Check aria-hidden="true" size={13} weight="bold" />
                ) : null}
                {filter.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => {
                setLayoutRevision((current) => current + 1);
                setSelectedId(null);
              }}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-line bg-canvas px-3 text-xs font-semibold text-ink-soft hover:border-line-strong hover:text-ink"
            >
              <ArrowsCounterClockwise aria-hidden="true" size={15} />
              Reset
            </button>
          </div>
        </div>
      </div>

      <div className="grid min-h-[37rem] xl:grid-cols-[minmax(0,1fr)_21rem]">
        <div
          className="relative h-[34rem] border-b border-line xl:h-[42rem] xl:border-r xl:border-b-0"
          role="region"
          aria-label={`${dossier.gene} interactive evidence graph`}
        >
          <ReactFlow<EvidenceNode, EvidenceEdge>
            nodes={displayNodes}
            edges={displayEdges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onNodeClick={(_, node) => focusNode(node.id)}
            onNodeDoubleClick={(_, node) => focusNode(node.id, true)}
            onNodeMouseEnter={(_, node) => setHoveredId(node.id)}
            onNodeMouseLeave={() => setHoveredId(null)}
            onPaneClick={() => setSelectedId(null)}
            onSelectionChange={handleSelectionChange}
            nodesConnectable={false}
            nodesDraggable
            nodesFocusable
            edgesFocusable
            edgesReconnectable={false}
            deleteKeyCode={null}
            zoomOnDoubleClick={false}
            minZoom={0.2}
            maxZoom={1.8}
            colorMode="dark"
            aria-label={`${dossier.gene} evidence lineage. Tab through nodes and edges; press Enter or Space to select.`}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={24}
              size={1}
              color="var(--graph-grid)"
            />
            <MiniMap
              className="evidence-minimap"
              pannable
              zoomable
              nodeColor={(node) => `var(--graph-${node.data.type})`}
              nodeStrokeColor="var(--line-strong)"
              nodeStrokeWidth={2}
              maskColor="rgba(8, 14, 12, 0.76)"
              aria-label="Evidence graph mini map"
            />
            <Controls
              position="bottom-left"
              showInteractive={false}
              fitViewOptions={{ padding: 0.17, duration: 320 }}
              aria-label="Evidence graph viewport controls"
            />
          </ReactFlow>

          {!layoutReady ? (
            <div className="absolute inset-0 z-20 grid place-items-center bg-surface/88 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-sm text-ink-soft">
                <CircleNotch aria-hidden="true" size={18} className="animate-spin" />
                Arranging evidence lineage
              </div>
            </div>
          ) : null}

          {activeLayoutError ? (
            <div className="absolute inset-x-4 top-4 z-20 border border-danger/35 bg-surface p-4 text-xs text-danger">
              {activeLayoutError}
            </div>
          ) : null}

          <button
            type="button"
            onClick={() =>
              void fitView({
                padding: 0.17,
                maxZoom: 1,
                duration: graphDuration(),
              })
            }
            className="absolute right-3 top-3 z-10 inline-flex min-h-11 items-center gap-2 rounded-lg border border-line-strong bg-surface/95 px-3 text-xs font-semibold text-ink shadow-lg backdrop-blur-sm hover:border-accent"
          >
            <ArrowsOutSimple aria-hidden="true" size={16} />
            Fit graph
          </button>
        </div>

        <aside className="bg-canvas/60 p-5" aria-live="polite">
          {inspected ? (
            <>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-accent">
                    {activeSelectedId ? inspected.eyebrow : "Graph overview"}
                  </p>
                  <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-ink">
                    {inspected.label}
                  </h3>
                </div>
                <div
                  className={`evidence-legend-dot evidence-legend-dot--${inspected.type}`}
                  aria-hidden="true"
                />
              </div>
              <p className="mt-2 font-mono text-xs text-accent-dark">
                {inspected.metric}
              </p>
              <p className="mt-4 text-sm leading-6 text-ink-soft">
                {inspected.detail}
              </p>
              {!activeSelectedId ? (
                <p className="mt-4 border-l-2 border-accent/45 pl-3 text-xs leading-5 text-ink-faint">
                  Select a node to lock its one-hop neighborhood. Hovering gives a
                  temporary preview.
                </p>
              ) : null}

              <div className="mt-5 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => focusNode(inspected.id, true)}
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-lg bg-accent px-3 text-xs font-semibold text-canvas hover:bg-accent-dark"
                >
                  <Target aria-hidden="true" size={15} />
                  Center node
                </button>
                {activeSelectedId ? (
                  <button
                    type="button"
                    onClick={() => setSelectedId(null)}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-line-strong bg-surface px-3 text-xs font-semibold text-ink hover:border-accent"
                  >
                    <X aria-hidden="true" size={14} />
                    Clear
                  </button>
                ) : null}
              </div>

              <div className="mt-7 border-t border-line pt-5">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold text-ink">Connected evidence</p>
                  <span className="font-mono text-[0.65rem] text-ink-faint">
                    {incoming.length + outgoing.length} direct
                  </span>
                </div>

                {incoming.length ? (
                  <div className="mt-3">
                    <p className="mb-1 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-ink-faint">
                      Connected from
                    </p>
                    {incoming.map((edge) => relationButton(edge, true))}
                  </div>
                ) : null}

                {outgoing.length ? (
                  <div className="mt-4">
                    <p className="mb-1 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-ink-faint">
                      Connects to
                    </p>
                    {outgoing.map((edge) => relationButton(edge, false))}
                  </div>
                ) : null}

                {!incoming.length && !outgoing.length ? (
                  <p className="mt-3 text-xs leading-5 text-ink-faint">
                    No visible direct relations under the active filters.
                  </p>
                ) : null}
              </div>
            </>
          ) : null}

          <details className="mt-7 border-t border-line pt-5">
            <summary className="cursor-pointer text-xs font-semibold text-ink">
              Relation vocabulary
            </summary>
            <dl className="mt-4 space-y-3 text-xs">
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Derived from</dt>
                <dd className="text-right text-ink">Computed lineage</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Source annotation</dt>
                <dd className="text-right text-ink">Not replication</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-soft">Not measured</dt>
                <dd className="text-right text-ink">Evidence gap</dd>
              </div>
            </dl>
          </details>
        </aside>
      </div>
    </section>
  );
}

export function EvidenceGraph({ dossier }: { dossier: GeneDossier }) {
  return (
    <ReactFlowProvider>
      <GraphWorkspace dossier={dossier} />
    </ReactFlowProvider>
  );
}
