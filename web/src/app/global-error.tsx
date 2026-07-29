"use client";

import { ErrorPanel } from "@/components/error-panel";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <head>
        <title>Workspace error · T-cell Evidence Workbench</title>
      </head>
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          background: "#0d1815",
          color: "#e8f0ec",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <ErrorPanel error={error} reset={reset} global />
      </body>
    </html>
  );
}
