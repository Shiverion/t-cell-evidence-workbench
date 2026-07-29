import "server-only";

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { unstable_cache } from "next/cache";

import {
  CONDITIONS,
  type ArtifactFile,
  type CandidateRow,
  type Condition,
  type CrossConditionCandidate,
  type DashboardData,
  type FunnelRow,
  type GeneDossier,
  type ManifestSummary,
  type PolarizationCoefficient,
  type RunSummary,
  type SourceFile,
  type ValidationSummary,
} from "@/lib/types";

type CsvRecord = Record<string, string>;

const outputDirectory = process.env.ANALYSIS_OUTPUT_DIR
  ? path.resolve(process.env.ANALYSIS_OUTPUT_DIR)
  : process.env.VERCEL
    ? path.resolve(process.cwd(), ".analysis-output", "official")
    : path.resolve(process.cwd(), "..", "output", "official");
const manifestFile = path.join(outputDirectory, "provenance", "manifest.json");
const manifestBytes = readFileSync(manifestFile);
const manifestSource = manifestBytes.toString("utf8");
const manifestIntegrity = JSON.parse(manifestSource) as {
  artifacts: Array<{ path: string; sha256: string }>;
};
const expectedArtifactHashes = new Map<string, string>();
for (const artifact of manifestIntegrity.artifacts) {
  const normalizedPath = artifact.path.replaceAll("\\", "/");
  expectedArtifactHashes.set(normalizedPath, artifact.sha256);
  if (path.isAbsolute(artifact.path)) {
    const relativePath = path.relative(outputDirectory, artifact.path);
    if (!relativePath.startsWith("..") && !path.isAbsolute(relativePath)) {
      expectedArtifactHashes.set(relativePath.replaceAll("\\", "/"), artifact.sha256);
    }
  }
}
const bundleFingerprint = createHash("sha256")
  .update(manifestBytes)
  .digest("hex");
const bundleCacheKey = ["analysis-bundle", bundleFingerprint];

async function readArtifact(relativePath: string) {
  const normalizedPath = relativePath.replaceAll("\\", "/");
  const expectedHash = expectedArtifactHashes.get(normalizedPath);
  if (!expectedHash) {
    throw new Error(`Artifact "${normalizedPath}" is not registered in the pinned manifest`);
  }
  const source = await readFile(path.join(outputDirectory, ...normalizedPath.split("/")));
  const actualHash = createHash("sha256").update(source).digest("hex");
  if (actualHash !== expectedHash) {
    throw new Error(
      `Artifact "${normalizedPath}" changed after the analysis bundle was pinned`,
    );
  }
  return source.toString("utf8");
}

async function readCsv(filename: string): Promise<CsvRecord[]> {
  const source = await readArtifact(`tables/${filename}`);
  return parse(source, {
    columns: true,
    skip_empty_lines: true,
    trim: true,
  }) as CsvRecord[];
}

function numberValue(record: CsvRecord, key: string) {
  if (record[key] == null || record[key].trim() === "") {
    throw new Error(`Expected numeric value for ${key}, received a blank cell`);
  }
  const value = Number(record[key]);
  if (!Number.isFinite(value)) {
    throw new Error(`Expected numeric value for ${key}, received "${record[key]}"`);
  }
  return value;
}

function nullableNumberValue(record: CsvRecord, key: string) {
  if (record[key] == null || record[key].trim() === "") return null;
  return numberValue(record, key);
}

function conditionValue(record: CsvRecord, key = "culture_condition"): Condition {
  const condition = record[key] as Condition;
  if (!CONDITIONS.includes(condition)) {
    throw new Error(`Unexpected culture condition "${record[key]}"`);
  }
  return condition;
}

function booleanValue(value: string) {
  const normalized = value.trim().toLowerCase();
  if (normalized === "true") return true;
  if (normalized === "false") return false;
  throw new Error(`Expected boolean value, received "${value}"`);
}

function parseCandidate(record: CsvRecord): CandidateRow {
  return {
    gene: record.gene,
    cultureCondition: conditionValue(record),
    targetContrast: record.target_contrast,
    nCellsTarget: numberValue(record, "n_cells_target"),
    nDownstream: numberValue(record, "n_downstream"),
    ontargetEffectSize: numberValue(record, "ontarget_effect_size"),
    crossdonorMin: numberValue(record, "crossdonor_min"),
    crossguide: numberValue(record, "crossguide"),
    nDownstreamPercentile: numberValue(record, "n_downstream_percentile"),
    crossdonorMinPercentile: numberValue(record, "crossdonor_min_percentile"),
    crossguidePercentile: numberValue(record, "crossguide_percentile"),
    priorityScore: numberValue(record, "priority_score"),
    rankWithinCondition: numberValue(record, "rank_within_condition"),
    candidateLabel: record.candidate_label,
  };
}

function parseCrossCandidate(record: CsvRecord): CrossConditionCandidate {
  return {
    gene: record.gene,
    scores: {
      Rest: numberValue(record, "Rest_priority_score"),
      Stim8hr: numberValue(record, "Stim8hr_priority_score"),
      Stim48hr: numberValue(record, "Stim48hr_priority_score"),
    },
    minPriorityScore: numberValue(record, "min_priority_score"),
    meanPriorityScore: numberValue(record, "mean_priority_score"),
    worstCondition: conditionValue(record, "worst_condition"),
    crossConditionRank: numberValue(record, "cross_condition_rank"),
    candidateLabel: record.candidate_label,
  };
}

function parseCoefficient(record: CsvRecord): PolarizationCoefficient {
  const signature = record.signature;
  if (signature !== "ota" && signature !== "activation") {
    throw new Error(`Unexpected polarization signature "${signature}"`);
  }
  const sourceRegulatorType = record.regulator_type.trim();
  let regulatorType: PolarizationCoefficient["regulatorType"] = null;
  if (
    sourceRegulatorType === "Th1 regulator" ||
    sourceRegulatorType === "Th2 regulator"
  ) {
    regulatorType = sourceRegulatorType;
  } else if (sourceRegulatorType) {
    throw new Error(`Unexpected regulator type "${sourceRegulatorType}"`);
  }

  return {
    coefficientMean: numberValue(record, "coef_mean"),
    coefficientSem: numberValue(record, "coef_sem"),
    coefficientRank: numberValue(record, "coef_rank"),
    regulator: record.regulator,
    knownRegulator: booleanValue(record.known_regulators),
    datasetKey: record.dataset_key,
    regulatorType: regulatorType || null,
    celltype: conditionValue(record, "celltype"),
    signature,
  };
}

function parseValidation(record: CsvRecord): ValidationSummary {
  return {
    perturbation: record.perturbation,
    nDonors: numberValue(record, "n_donors"),
    il10MeanDelta: nullableNumberValue(record, "IL10_mean_delta"),
    il10MedianDelta: nullableNumberValue(record, "IL10_median_delta"),
    il10MinDelta: nullableNumberValue(record, "IL10_min_delta"),
    il10MaxDelta: nullableNumberValue(record, "IL10_max_delta"),
    il21MeanDelta: nullableNumberValue(record, "IL21_mean_delta"),
    il21MedianDelta: nullableNumberValue(record, "IL21_median_delta"),
    il21MinDelta: nullableNumberValue(record, "IL21_min_delta"),
    il21MaxDelta: nullableNumberValue(record, "IL21_max_delta"),
  };
}

export const getCandidates = unstable_cache(
  async () => (await readCsv("candidate_scores.csv")).map(parseCandidate),
  [...bundleCacheKey, "candidates"],
  { revalidate: false },
);

export const getCrossCandidates = unstable_cache(
  async () => (await readCsv("cross_condition_candidates.csv")).map(parseCrossCandidate),
  [...bundleCacheKey, "cross-candidates"],
  { revalidate: false },
);

export const getTopCandidates = unstable_cache(
  async () => (await readCsv("top_candidates_by_condition.csv")).map(parseCandidate),
  [...bundleCacheKey, "top-candidates"],
  { revalidate: false },
);

export const getFunnel = unstable_cache(
  async (): Promise<FunnelRow[]> =>
    (await readCsv("filter_funnel.csv")).map((record) => ({
      cultureCondition: conditionValue(record),
      stageOrder: numberValue(record, "stage_order"),
      stage: record.stage,
      nRows: numberValue(record, "n_rows"),
    })),
  [...bundleCacheKey, "funnel"],
  { revalidate: false },
);

export const getCoefficients = unstable_cache(
  async () =>
    (await readCsv("candidate_polarization_coefficients.csv")).map(parseCoefficient),
  [...bundleCacheKey, "coefficients"],
  { revalidate: false },
);

export const getValidationSummaries = unstable_cache(
  async () => (await readCsv("validation_summary.csv")).map(parseValidation),
  [...bundleCacheKey, "validation-summaries"],
  { revalidate: false },
);

export const getRunSummary = unstable_cache(
  async (): Promise<RunSummary> => {
    const raw = JSON.parse(
      await readArtifact("run_summary.json"),
    ) as {
      status: string;
      cross_condition_candidate_count: number;
      lead_cross_condition_candidate: {
        gene: string;
        min_priority_score: number;
        worst_condition: Condition;
      } | null;
      source_qc_passes_by_condition: Record<Condition, number>;
    };

    return {
      status: raw.status,
      crossConditionCandidateCount: raw.cross_condition_candidate_count,
      leadCrossConditionCandidate: raw.lead_cross_condition_candidate
        ? {
            gene: raw.lead_cross_condition_candidate.gene,
            minPriorityScore: raw.lead_cross_condition_candidate.min_priority_score,
            worstCondition: raw.lead_cross_condition_candidate.worst_condition,
          }
        : null,
      sourceQcPassesByCondition: raw.source_qc_passes_by_condition,
    };
  },
  [...bundleCacheKey, "run-summary"],
  { revalidate: false },
);

export const getManifest = unstable_cache(
  async (): Promise<ManifestSummary> => {
    const raw = JSON.parse(manifestSource) as {
      workflow: string;
      generated_at_utc: string;
      pinned_commit: string;
      analysis_contract: {
        conditions: Condition[];
        min_cells_target: number;
        top_n: number;
        hard_gates: Record<string, string | number | boolean>;
      };
      source_files: SourceFile[];
      artifacts: ArtifactFile[];
      package_versions: Record<string, string>;
    };

    return {
      workflow: raw.workflow,
      generatedAtUtc: raw.generated_at_utc,
      pinnedCommit: raw.pinned_commit,
      analysisContract: {
        conditions: raw.analysis_contract.conditions,
        minCellsTarget: raw.analysis_contract.min_cells_target,
        topN: raw.analysis_contract.top_n,
        hardGates: raw.analysis_contract.hard_gates,
      },
      sourceFiles: raw.source_files,
      artifacts: raw.artifacts,
      packageVersions: raw.package_versions,
    };
  },
  [...bundleCacheKey, "manifest"],
  { revalidate: false },
);

export const getDashboardData = unstable_cache(
  async (): Promise<DashboardData> => {
    const [runSummary, funnel, topCandidates, crossCandidates] = await Promise.all([
      getRunSummary(),
      getFunnel(),
      getTopCandidates(),
      getCrossCandidates(),
    ]);
    return { runSummary, funnel, topCandidates, crossCandidates };
  },
  [...bundleCacheKey, "dashboard"],
  { revalidate: false },
);

export const getGeneDossier = unstable_cache(
  async (geneInput: string): Promise<GeneDossier | null> => {
    const gene = geneInput.trim().toUpperCase();
    const [candidates, crossCandidates, coefficients, validations] = await Promise.all([
      getCandidates(),
      getCrossCandidates(),
      getCoefficients(),
      getValidationSummaries(),
    ]);
    const conditionRows = candidates.filter((row) => row.gene === gene);
    if (conditionRows.length === 0) return null;

    return {
      gene,
      conditionRows: conditionRows.sort(
        (left, right) =>
          CONDITIONS.indexOf(left.cultureCondition) -
          CONDITIONS.indexOf(right.cultureCondition),
      ),
      crossCondition: crossCandidates.find((row) => row.gene === gene) ?? null,
      coefficients: coefficients
        .filter((row) => row.regulator === gene)
        .sort((left, right) => right.coefficientRank - left.coefficientRank)
        .slice(0, 10),
      validation: validations.find((row) => row.perturbation === gene) ?? null,
    };
  },
  [...bundleCacheKey, "gene-dossier"],
  { revalidate: false },
);

export const getGeneNames = unstable_cache(
  async () => {
    const candidates = await getCandidates();
    return [...new Set(candidates.map((row) => row.gene))].sort((left, right) =>
      left.localeCompare(right),
    );
  },
  [...bundleCacheKey, "gene-names"],
  { revalidate: false },
);

export function getOutputDirectory() {
  return outputDirectory;
}

export function getBundleFingerprint() {
  return bundleFingerprint;
}
