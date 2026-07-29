export const CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"] as const;

export type Condition = (typeof CONDITIONS)[number];

export type CandidateRow = {
  gene: string;
  cultureCondition: Condition;
  targetContrast: string;
  nCellsTarget: number;
  nDownstream: number;
  ontargetEffectSize: number;
  crossdonorMin: number;
  crossguide: number;
  nDownstreamPercentile: number;
  crossdonorMinPercentile: number;
  crossguidePercentile: number;
  priorityScore: number;
  rankWithinCondition: number;
  candidateLabel: string;
};

export type CrossConditionCandidate = {
  gene: string;
  scores: Record<Condition, number>;
  minPriorityScore: number;
  meanPriorityScore: number;
  worstCondition: Condition;
  crossConditionRank: number;
  candidateLabel: string;
};

export type PolarizationCoefficient = {
  coefficientMean: number;
  coefficientSem: number;
  coefficientRank: number;
  regulator: string;
  knownRegulator: boolean;
  datasetKey: string;
  regulatorType: "Th1 regulator" | "Th2 regulator" | null;
  celltype: Condition;
  signature: "ota" | "activation";
};

export type ValidationSummary = {
  perturbation: string;
  nDonors: number;
  il10MeanDelta: number | null;
  il10MedianDelta: number | null;
  il10MinDelta: number | null;
  il10MaxDelta: number | null;
  il21MeanDelta: number | null;
  il21MedianDelta: number | null;
  il21MinDelta: number | null;
  il21MaxDelta: number | null;
};

export type FunnelRow = {
  cultureCondition: Condition;
  stageOrder: number;
  stage: string;
  nRows: number;
};

export type RunSummary = {
  status: string;
  crossConditionCandidateCount: number;
  leadCrossConditionCandidate: {
    gene: string;
    minPriorityScore: number;
    worstCondition: Condition;
  } | null;
  sourceQcPassesByCondition: Record<Condition, number>;
};

export type SourceFile = {
  key: string;
  path: string;
  url: string;
  bytes: number;
  sha256: string;
};

export type ArtifactFile = {
  path: string;
  bytes: number;
  sha256: string;
};

export type ManifestSummary = {
  workflow: string;
  generatedAtUtc: string;
  pinnedCommit: string;
  analysisContract: {
    conditions: Condition[];
    minCellsTarget: number;
    topN: number;
    hardGates: Record<string, string | number | boolean>;
  };
  sourceFiles: SourceFile[];
  artifacts: ArtifactFile[];
  packageVersions: Record<string, string>;
};

export type GeneDossier = {
  gene: string;
  conditionRows: CandidateRow[];
  crossCondition: CrossConditionCandidate | null;
  coefficients: PolarizationCoefficient[];
  validation: ValidationSummary | null;
};

export type DashboardData = {
  runSummary: RunSummary;
  funnel: FunnelRow[];
  topCandidates: CandidateRow[];
  crossCandidates: CrossConditionCandidate[];
};
