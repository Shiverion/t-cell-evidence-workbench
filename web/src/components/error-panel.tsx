"use client";

import { SealWarning } from "@phosphor-icons/react";
import { useEffect } from "react";

import { reportClientError } from "@/components/client-error-monitor";
import { safeErrorDigest } from "@/lib/error-monitoring";

export function ErrorPanel({
  error,
  reset,
  global = false,
}: {
  error: Error & { digest?: string };
  reset: () => void;
  global?: boolean;
}) {
  const artifactError =
    /(?:ENOENT|artifact|manifest|analysis bundle|output[\\/]+official)/i.test(
      error.message,
    );
  const reference = safeErrorDigest(error.digest);

  useEffect(() => {
    reportClientError("render", error, reference);
  }, [error, reference]);

  return (
    <div className={global ? "grid min-h-[100dvh] place-items-center px-4" : "grid min-h-[60dvh] place-items-center"}>
      <div className="w-full max-w-xl border border-danger/30 bg-surface p-7">
        <SealWarning aria-hidden="true" size={28} className="text-danger" />
        <h1 className="mt-6 text-2xl font-semibold tracking-[-0.04em] text-ink">
          {artifactError
            ? "The analysis artifacts could not be loaded."
            : "The analyst workspace encountered an error."}
        </h1>
        <p className="mt-3 text-sm leading-6 text-ink-soft">
          {artifactError
            ? "The pinned analysis bundle is unavailable or failed its integrity check. The incident has been recorded without collecting reviewer input."
            : "Retry the current view. A privacy-scrubbed technical event has been recorded for review."}
        </p>
        {reference ? (
          <p className="mt-4 rounded-lg bg-surface-strong p-3 font-mono text-xs text-ink-soft">
            Error reference: {reference}
          </p>
        ) : null}
        <button
          type="button"
          onClick={reset}
          className="mt-6 min-h-10 rounded-lg bg-ink px-4 text-sm font-semibold text-canvas hover:bg-accent-dark"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
