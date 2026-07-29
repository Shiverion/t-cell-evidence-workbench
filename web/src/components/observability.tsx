"use client";

import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";

function normalizeAnalyticsPath(pathname: string) {
  if (/^\/genes\/[^/]+\/?$/.test(pathname)) return "/genes/[gene]";
  return pathname || "/";
}

function privacySafeUrl(value: string) {
  try {
    const url = new URL(value);
    url.pathname = normalizeAnalyticsPath(url.pathname);
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return normalizeAnalyticsPath(value.split(/[?#]/, 1)[0]);
  }
}

export function Observability() {
  return (
    <>
      <Analytics
        beforeSend={(event) => ({
          ...event,
          url: privacySafeUrl(event.url),
        })}
      />
      <SpeedInsights
        beforeSend={(event) => ({
          ...event,
          url: privacySafeUrl(event.url),
          route: event.route
            ? normalizeAnalyticsPath(event.route.split(/[?#]/, 1)[0])
            : event.route,
        })}
      />
    </>
  );
}
