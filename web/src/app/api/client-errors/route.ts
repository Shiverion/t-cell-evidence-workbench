import {
  CLIENT_ERROR_KINDS,
  normalizeTelemetryPath,
  safeErrorDigest,
  sanitizeErrorMessage,
  type ClientErrorKind,
} from "@/lib/error-monitoring";

const MAX_BODY_BYTES = 4096;
const allowedKinds = new Set<ClientErrorKind>(CLIENT_ERROR_KINDS);

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type") ?? "";
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  const requestOrigin = new URL(request.url).origin;
  const origin = request.headers.get("origin");

  if (origin && origin !== requestOrigin) {
    return Response.json({ error: "Cross-origin reports are not accepted." }, { status: 403 });
  }
  if (!contentType.toLowerCase().startsWith("application/json")) {
    return Response.json({ error: "Expected application/json." }, { status: 415 });
  }
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    return Response.json({ error: "Report is too large." }, { status: 413 });
  }

  const rawBody = await request.text();
  if (Buffer.byteLength(rawBody, "utf8") > MAX_BODY_BYTES) {
    return Response.json({ error: "Report is too large." }, { status: 413 });
  }

  let input: Record<string, unknown>;
  try {
    input = JSON.parse(rawBody) as Record<string, unknown>;
  } catch {
    return Response.json({ error: "Invalid JSON." }, { status: 400 });
  }

  const kind = typeof input.kind === "string" ? input.kind : "";
  if (!allowedKinds.has(kind as ClientErrorKind)) {
    return Response.json({ error: "Unsupported error kind." }, { status: 400 });
  }

  console.error(
    JSON.stringify({
      level: "error",
      event: "client_runtime_error",
      kind,
      message: sanitizeErrorMessage(input.message),
      route: normalizeTelemetryPath(
        typeof input.route === "string" ? input.route : "/other",
      ),
      digest: safeErrorDigest(input.digest),
      requestId: request.headers.get("x-vercel-id") ?? undefined,
      deployment:
        process.env.VERCEL_DEPLOYMENT_ID ??
        process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12),
    }),
  );

  return new Response(null, {
    status: 204,
    headers: { "Cache-Control": "no-store" },
  });
}
