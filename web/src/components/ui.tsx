import Link from "next/link";

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-accent">
      {children}
    </p>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="mb-9 grid gap-6 border-b border-line pb-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
      <div>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h1 className="max-w-4xl text-3xl font-semibold leading-[1.05] tracking-[-0.045em] text-ink sm:text-4xl">
          {title}
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-ink-soft sm:text-base">
          {description}
        </p>
      </div>
      {action ? <div className="flex items-center gap-3">{action}</div> : null}
    </header>
  );
}

export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "accent" | "success" | "warning" | "danger";
}) {
  const tones = {
    neutral: "border-line bg-surface-strong text-ink-soft",
    accent: "border-accent/20 bg-accent-soft text-accent-dark",
    success: "border-success/20 bg-success/10 text-success",
    warning: "border-warning/20 bg-warning/10 text-warning",
    danger: "border-danger/20 bg-danger/10 text-danger",
  };
  return (
    <span
      className={`inline-flex min-h-6 items-center rounded-full border px-2.5 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.08em] ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function PrimaryLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-10 items-center justify-center rounded-lg bg-ink px-4 text-sm font-semibold text-canvas hover:bg-accent-dark"
    >
      {children}
    </Link>
  );
}

export function SecondaryLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-10 items-center justify-center rounded-lg border border-line-strong bg-surface px-4 text-sm font-semibold text-ink hover:border-accent hover:text-accent-dark"
    >
      {children}
    </Link>
  );
}

export function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: React.ReactNode;
  detail?: React.ReactNode;
}) {
  return (
    <div className="min-w-0 py-5">
      <p className="text-xs font-medium text-ink-faint">{label}</p>
      <p className="numeric mt-2 font-mono text-2xl font-medium tracking-[-0.04em] text-ink">
        {value}
      </p>
      {detail ? <p className="mt-1 text-xs leading-5 text-ink-soft">{detail}</p> : null}
    </div>
  );
}

export function SectionHeader({
  title,
  description,
  trailing,
}: {
  title: string;
  description?: string;
  trailing?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
      <div>
        <h2 className="text-xl font-semibold tracking-[-0.03em] text-ink">{title}</h2>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm leading-6 text-ink-soft">{description}</p>
        ) : null}
      </div>
      {trailing}
    </div>
  );
}

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="grid min-h-48 place-items-center border border-dashed border-line-strong bg-surface/45 px-6 text-center">
      <div>
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-2 max-w-md text-sm leading-6 text-ink-soft">{description}</p>
      </div>
    </div>
  );
}
