const EMAIL_PATTERN = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const URL_PATTERN = /https?:\/\/[^\s)]+/gi;
const WINDOWS_PATH_PATTERN = /\b[A-Z]:\\(?:[^\\\s]+\\)*[^\\\s]*/gi;
const HOME_PATH_PATTERN = /\/(?:Users|home)\/[^/\s]+(?:\/[^\s]*)?/gi;

export const CLIENT_ERROR_KINDS = [
  "render",
  "uncaught",
  "unhandled-rejection",
] as const;

export type ClientErrorKind = (typeof CLIENT_ERROR_KINDS)[number];

export function sanitizeErrorMessage(value: unknown) {
  const message =
    value instanceof Error
      ? value.message
      : typeof value === "string"
        ? value
        : "Unknown application error";

  return message
    .replace(EMAIL_PATTERN, "[redacted-email]")
    .replace(URL_PATTERN, "[redacted-url]")
    .replace(WINDOWS_PATH_PATTERN, "[local-path]")
    .replace(HOME_PATH_PATTERN, "[local-path]")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 400);
}

export function normalizeTelemetryPath(value: string) {
  const pathname = value.split(/[?#]/, 1)[0] || "/";

  if (/^\/genes\/[^/]+\/?$/.test(pathname)) return "/genes/[gene]";
  if (pathname.startsWith("/api/client-errors")) return "/api/client-errors";

  const publicRoutes = new Set([
    "/",
    "/compare",
    "/explore",
    "/findings",
    "/provenance",
    "/robustness",
  ]);

  return publicRoutes.has(pathname) ? pathname : "/other";
}

export function safeErrorDigest(value: unknown) {
  if (typeof value !== "string") return undefined;
  const digest = value.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 80);
  return digest || undefined;
}
