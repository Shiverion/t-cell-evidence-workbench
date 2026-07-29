"use client";

import {
  ArrowsLeftRight,
  BookOpenText,
  CirclesThree,
  ClockCounterClockwise,
  Fingerprint,
  Flask,
  House,
  ListMagnifyingGlass,
  NotePencil,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ReviewerTools } from "@/components/reviewer-tools";

function Navigation({
  defaultGene,
  onNavigate,
}: {
  defaultGene: string | null;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const navigation = [
    { href: "/", label: "Overview", icon: House },
    { href: "/explore", label: "Candidate explorer", icon: ListMagnifyingGlass },
    {
      href: defaultGene ? `/genes/${defaultGene}` : "/explore",
      activePath: "/genes",
      label: "Evidence graph",
      icon: CirclesThree,
    },
    { href: "/compare", label: "Compare genes", icon: ArrowsLeftRight },
    { href: "/robustness", label: "Robustness lab", icon: SlidersHorizontal },
    { href: "/findings", label: "Finding cards", icon: NotePencil },
    { href: "/provenance", label: "Provenance", icon: ShieldCheck },
  ] as const;

  return (
    <nav aria-label="Primary navigation" className="flex flex-col gap-1">
      {navigation.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname.startsWith("activePath" in item ? item.activePath : item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`group flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium ${
              active
                ? "bg-accent-soft text-accent-dark"
                : "text-ink-soft hover:bg-surface-strong hover:text-ink"
            }`}
          >
            <Icon
              aria-hidden="true"
              size={19}
              weight={active ? "fill" : "regular"}
              className="shrink-0"
            />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

function Brand() {
  return (
    <Link href="/" className="flex items-center gap-3" aria-label="T-cell Evidence Workbench home">
      <span className="grid size-10 place-items-center rounded-xl bg-accent text-canvas shadow-[0_12px_28px_-16px_var(--shadow)]">
        <Flask aria-hidden="true" size={21} weight="duotone" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold tracking-[-0.02em] text-ink">
          T-cell Evidence
        </span>
        <span className="block text-xs text-ink-faint">Analyst workbench</span>
      </span>
    </Link>
  );
}

function AnalysisIdentity({
  generatedAtUtc,
  generatedAtLabel,
  bundleFingerprint,
}: {
  generatedAtUtc: string;
  generatedAtLabel: string;
  bundleFingerprint: string;
}) {
  return (
    <Link
      href="/provenance"
      className="block rounded-lg border border-line bg-accent-soft/22 p-3 hover:border-accent/55 hover:bg-accent-soft/35"
    >
      <span className="flex items-center gap-2 font-mono text-[0.64rem] font-semibold uppercase tracking-[0.12em] text-accent">
        <Fingerprint aria-hidden="true" size={15} />
        Pinned analysis bundle
      </span>
      <span className="mt-3 flex items-start gap-2 text-xs leading-5 text-ink-soft">
        <ClockCounterClockwise
          aria-hidden="true"
          size={15}
          className="mt-0.5 shrink-0 text-ink-faint"
        />
        <time dateTime={generatedAtUtc}>Generated {generatedAtLabel}</time>
      </span>
      <span
        className="mt-2 block truncate font-mono text-[0.65rem] text-ink-faint"
        title={`Manifest SHA-256 ${bundleFingerprint}`}
        aria-label={`Manifest SHA-256 ${bundleFingerprint}`}
      >
        sha256 {bundleFingerprint.slice(0, 12)}…
      </span>
    </Link>
  );
}

export function AppShell({
  children,
  defaultGene,
  generatedAtUtc,
  generatedAtLabel,
  bundleFingerprint,
  feedbackEmail,
}: {
  children: React.ReactNode;
  defaultGene: string | null;
  generatedAtUtc: string;
  generatedAtLabel: string;
  bundleFingerprint: string;
  feedbackEmail?: string;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!mobileOpen) return;

    const previousOverflow = document.body.style.overflow;
    const opener = menuButtonRef.current;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileOpen(false);
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;

      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      opener?.focus();
    };
  }, [mobileOpen]);

  return (
    <div className="min-h-[100dvh]">
      <aside
        inert={mobileOpen}
        className="fixed inset-y-0 left-0 hidden w-[var(--sidebar-width)] border-r border-line bg-surface/97 px-4 py-5 backdrop-blur-sm lg:flex lg:flex-col"
      >
        <Brand />
        <div className="mt-9 flex-1">
          <Navigation defaultGene={defaultGene} />
        </div>
        <div className="space-y-3 border-t border-line pt-4">
          <AnalysisIdentity
            generatedAtUtc={generatedAtUtc}
            generatedAtLabel={generatedAtLabel}
            bundleFingerprint={bundleFingerprint}
          />
          <div className="flex items-start gap-2.5 rounded-lg bg-surface-strong/65 p-3">
            <BookOpenText aria-hidden="true" size={18} className="mt-0.5 shrink-0 text-accent" />
            <p className="text-xs leading-5 text-ink-soft">
              Registered analysis remains distinct from every exploratory view.
            </p>
          </div>
        </div>
      </aside>

      <header
        inert={mobileOpen}
        aria-hidden={mobileOpen || undefined}
        className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-canvas/95 px-4 backdrop-blur-md lg:hidden"
      >
        <Brand />
        <button
          ref={menuButtonRef}
          type="button"
          aria-label="Open navigation"
          aria-expanded={mobileOpen}
          aria-controls="mobile-navigation-dialog"
          onClick={() => setMobileOpen((current) => !current)}
          className="grid size-10 place-items-center rounded-lg border border-line bg-surface text-ink"
        >
          <ListMagnifyingGlass size={20} />
        </button>
      </header>

      {mobileOpen ? (
        <div
          ref={dialogRef}
          id="mobile-navigation-dialog"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
          className="fixed inset-0 z-30 overflow-y-auto bg-canvas/98 backdrop-blur-md lg:hidden"
        >
          <div className="sticky top-0 flex h-16 items-center justify-between border-b border-line bg-canvas px-4">
            <Brand />
            <button
              ref={closeButtonRef}
              type="button"
              aria-label="Close navigation"
              onClick={() => setMobileOpen(false)}
              className="grid size-10 place-items-center rounded-lg border border-line bg-surface text-ink"
            >
              <X aria-hidden="true" size={20} />
            </button>
          </div>
          <div className="px-4 py-6">
            <Navigation
              defaultGene={defaultGene}
              onNavigate={() => setMobileOpen(false)}
            />
            <div className="mt-6 border-t border-line pt-5">
              <AnalysisIdentity
                generatedAtUtc={generatedAtUtc}
                generatedAtLabel={generatedAtLabel}
                bundleFingerprint={bundleFingerprint}
              />
            </div>
          </div>
        </div>
      ) : null}

      <main
        inert={mobileOpen}
        aria-hidden={mobileOpen || undefined}
        className="min-h-[100dvh] lg:pl-[var(--sidebar-width)]"
      >
        <div className="mx-auto w-full max-w-[1480px] px-4 py-8 sm:px-7 lg:px-10 lg:py-10">
          <div className="page-enter">{children}</div>
        </div>
        <ReviewerTools
          defaultGene={defaultGene}
          bundleFingerprint={bundleFingerprint}
          generatedAtLabel={generatedAtLabel}
          feedbackEmail={feedbackEmail}
        />
      </main>
    </div>
  );
}
