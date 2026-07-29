import path from "node:path";

import type { NextConfig } from "next";

const repositoryRoot = path.resolve(process.cwd(), "..");
const analysisArtifacts = [
  ".analysis-output/official/**/*",
  "../output/official/**/*",
];

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  outputFileTracingRoot: repositoryRoot,
  outputFileTracingIncludes: {
    "/*": analysisArtifacts,
    "/compare": analysisArtifacts,
    "/findings": analysisArtifacts,
    "/genes/*": analysisArtifacts,
  },
  turbopack: {
    root: repositoryRoot,
  },
};

export default nextConfig;
