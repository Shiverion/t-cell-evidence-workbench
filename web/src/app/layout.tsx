import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { AppShell } from "@/components/app-shell";
import { ClientErrorMonitor } from "@/components/client-error-monitor";
import { Observability } from "@/components/observability";
import {
  getBundleFingerprint,
  getGeneNames,
  getManifest,
  getRunSummary,
} from "@/lib/data";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteName = "T-cell Evidence Workbench";
const siteDescription =
  "Traceable exploration of source-QC candidates from the Primary Human CD4+ T Cell Perturb-seq dataset.";
const deploymentHost =
  process.env.VERCEL_ENV === "production"
    ? process.env.VERCEL_PROJECT_PRODUCTION_URL
    : process.env.VERCEL_URL;
const metadataBase = new URL(
  process.env.NEXT_PUBLIC_SITE_URL ??
    (deploymentHost ? `https://${deploymentHost}` : "http://localhost:3000"),
);

export const metadata: Metadata = {
  metadataBase,
  applicationName: siteName,
  title: {
    default: "T-cell Evidence Workbench",
    template: "%s · T-cell Evidence Workbench",
  },
  description: siteDescription,
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    siteName,
    title: siteName,
    description: siteDescription,
  },
  twitter: {
    card: "summary_large_image",
    title: siteName,
    description: siteDescription,
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [runSummary, geneNames, manifest] = await Promise.all([
    getRunSummary(),
    getGeneNames(),
    getManifest(),
  ]);
  const defaultGene = runSummary.leadCrossConditionCandidate?.gene ?? geneNames[0] ?? null;
  const generatedDate = new Date(manifest.generatedAtUtc);
  const generatedAtLabel = `${new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(generatedDate)} · ${new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    hourCycle: "h23",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(generatedDate)} UTC`;
  const bundleFingerprint = getBundleFingerprint();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable}`}
      data-scroll-behavior="smooth"
    >
      <body>
        <AppShell
          defaultGene={defaultGene}
          generatedAtUtc={manifest.generatedAtUtc}
          generatedAtLabel={generatedAtLabel}
          bundleFingerprint={bundleFingerprint}
          feedbackEmail={process.env.NEXT_PUBLIC_REVIEW_FEEDBACK_EMAIL}
        >
          {children}
        </AppShell>
        <ClientErrorMonitor />
        <Observability />
      </body>
    </html>
  );
}
