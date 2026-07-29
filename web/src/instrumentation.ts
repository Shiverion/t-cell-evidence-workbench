import type { Instrumentation } from "next";

import {
  normalizeTelemetryPath,
  safeErrorDigest,
  sanitizeErrorMessage,
} from "@/lib/error-monitoring";

export const onRequestError: Instrumentation.onRequestError = async (
  error,
  errorRequest,
  context,
) => {
  const digest =
    error && typeof error === "object" && "digest" in error
      ? safeErrorDigest(error.digest)
      : undefined;

  console.error(
    JSON.stringify({
      level: "error",
      event: "next_request_error",
      message: sanitizeErrorMessage(error),
      digest,
      route: normalizeTelemetryPath(context.routePath),
      routeType: context.routeType,
      renderSource: context.renderSource,
      routerKind: context.routerKind,
      method: errorRequest.method,
      runtime: process.env.NEXT_RUNTIME ?? "nodejs",
      deployment:
        process.env.VERCEL_DEPLOYMENT_ID ??
        process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12),
    }),
  );
};
