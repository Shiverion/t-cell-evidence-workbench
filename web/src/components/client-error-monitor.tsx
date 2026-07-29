"use client";

import { useEffect } from "react";

import {
  normalizeTelemetryPath,
  safeErrorDigest,
  sanitizeErrorMessage,
  type ClientErrorKind,
} from "@/lib/error-monitoring";

const reportedEvents = new Set<string>();

export function reportClientError(
  kind: ClientErrorKind,
  error: unknown,
  digest?: string,
) {
  if (process.env.NODE_ENV !== "production" || typeof window === "undefined") return;

  const payload = {
    kind,
    message: sanitizeErrorMessage(error),
    route: normalizeTelemetryPath(window.location.pathname),
    digest: safeErrorDigest(digest),
  };
  const eventKey = JSON.stringify(payload);

  if (reportedEvents.has(eventKey)) return;
  if (reportedEvents.size >= 20) {
    const oldest = reportedEvents.values().next().value;
    if (oldest) reportedEvents.delete(oldest);
  }
  reportedEvents.add(eventKey);

  void fetch("/api/client-errors", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: eventKey,
    cache: "no-store",
    keepalive: true,
  }).catch(() => {
    // Monitoring must never interrupt the reviewer workflow.
  });
}

export function ClientErrorMonitor() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;

    function handleWindowError(event: ErrorEvent) {
      reportClientError("uncaught", event.error ?? event.message);
    }

    function handleUnhandledRejection(event: PromiseRejectionEvent) {
      reportClientError("unhandled-rejection", event.reason);
    }

    window.addEventListener("error", handleWindowError);
    window.addEventListener("unhandledrejection", handleUnhandledRejection);

    return () => {
      window.removeEventListener("error", handleWindowError);
      window.removeEventListener("unhandledrejection", handleUnhandledRejection);
    };
  }, []);

  return null;
}
