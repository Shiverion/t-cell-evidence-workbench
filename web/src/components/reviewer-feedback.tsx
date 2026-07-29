"use client";

import {
  ChatCircleText,
  Check,
  Copy,
  DownloadSimple,
  EnvelopeSimple,
  ShieldCheck,
  X,
} from "@phosphor-icons/react";
import { useEffect, useId, useRef, useState } from "react";

const categories = [
  { value: "ux", label: "Interaction / UI" },
  { value: "science", label: "Scientific clarity" },
  { value: "bug", label: "Bug" },
  { value: "idea", label: "Idea" },
] as const;

type Category = (typeof categories)[number]["value"];
type FeedbackStatus = "idle" | "copied" | "downloaded" | "error";

export function ReviewerFeedback({
  bundleFingerprint,
  generatedAtLabel,
  feedbackEmail,
}: {
  bundleFingerprint: string;
  generatedAtLabel: string;
  feedbackEmail?: string;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<Category>("ux");
  const [notes, setNotes] = useState("");
  const [includePage, setIncludePage] = useState(false);
  const [status, setStatus] = useState<FeedbackStatus>("idle");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (!open) {
      if (dialog.open) dialog.close();
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (!dialog.open) dialog.showModal();
    window.requestAnimationFrame(() => textareaRef.current?.focus());

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  function closeDialog() {
    setOpen(false);
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  }

  function buildFeedbackMarkdown() {
    const selectedCategory =
      categories.find((item) => item.value === category)?.label ?? category;
    const page =
      includePage && typeof window !== "undefined"
        ? `${window.location.pathname}${window.location.search}`
        : "Not included";

    return [
      "# T-cell Evidence Workbench — reviewer feedback",
      "",
      `- Category: ${selectedCategory}`,
      `- Analysis generated: ${generatedAtLabel}`,
      `- Bundle SHA-256: ${bundleFingerprint}`,
      `- Page: ${page}`,
      "",
      "## Review note",
      "",
      notes.trim(),
      "",
      "> This note was prepared locally in the reviewer’s browser and was not transmitted automatically.",
    ].join("\n");
  }

  async function copyFeedback() {
    if (!notes.trim()) {
      setStatus("error");
      return;
    }
    try {
      await navigator.clipboard.writeText(buildFeedbackMarkdown());
      setStatus("copied");
    } catch {
      setStatus("error");
    }
  }

  function downloadFeedback() {
    if (!notes.trim()) {
      setStatus("error");
      return;
    }
    const blob = new Blob([buildFeedbackMarkdown()], {
      type: "text/markdown;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `t-cell-evidence-review-${new Date()
      .toISOString()
      .slice(0, 10)}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
    setStatus("downloaded");
  }

  function openEmailDraft() {
    if (!feedbackEmail || !notes.trim()) {
      setStatus("error");
      return;
    }
    const subject = encodeURIComponent("T-cell Evidence Workbench reviewer feedback");
    const body = encodeURIComponent(buildFeedbackMarkdown());
    window.location.href = `mailto:${encodeURIComponent(feedbackEmail)}?subject=${subject}&body=${body}`;
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => {
          setStatus("idle");
          setOpen(true);
        }}
        aria-haspopup="dialog"
        aria-label="Reviewer feedback"
        className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-line-strong bg-surface px-3 text-sm font-semibold text-ink shadow-[0_16px_40px_-28px_var(--shadow)] hover:border-accent hover:text-accent-dark"
      >
        <ChatCircleText aria-hidden="true" size={18} />
        Feedback
      </button>

      <dialog
        ref={dialogRef}
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onCancel={() => setOpen(false)}
        onClose={() => {
          setOpen(false);
          triggerRef.current?.focus();
        }}
        onClick={(event) => {
          if (event.target === dialogRef.current) closeDialog();
        }}
        className="reviewer-dialog m-auto max-h-[calc(100dvh-2rem)] w-[min(42rem,calc(100vw-2rem))] overflow-y-auto border border-line-strong bg-surface p-0 text-ink shadow-[0_32px_90px_-38px_var(--shadow)] backdrop:bg-canvas/82 backdrop:backdrop-blur-sm"
      >
        <div className="p-5 sm:p-7">
          <div className="flex items-start justify-between gap-5">
            <div>
              <p className="font-mono text-[0.66rem] font-semibold uppercase tracking-[0.14em] text-accent">
                Reviewer channel
              </p>
              <h2
                id={titleId}
                className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-ink"
              >
                Prepare a review note.
              </h2>
              <p
                id={descriptionId}
                className="mt-3 max-w-xl text-sm leading-6 text-ink-soft"
              >
                Capture an interaction issue, scientific ambiguity, bug, or idea in a
                reproducible Markdown note.
              </p>
            </div>
            <button
              type="button"
              onClick={closeDialog}
              aria-label="Close reviewer feedback"
              className="grid size-10 shrink-0 place-items-center rounded-lg border border-line bg-canvas text-ink-soft hover:border-accent hover:text-ink"
            >
              <X aria-hidden="true" size={18} />
            </button>
          </div>

          <div className="mt-6 flex items-start gap-3 border-y border-line bg-accent-soft/25 px-4 py-4">
            <ShieldCheck
              aria-hidden="true"
              size={20}
              className="mt-0.5 shrink-0 text-accent"
            />
            <p className="text-xs leading-5 text-ink-soft">
              Nothing is submitted automatically. No name, email address, device
              information, or feedback text is collected by analytics. You choose when
              to copy, download, or open an email draft.
            </p>
          </div>

          <fieldset className="mt-6">
            <legend className="text-xs font-semibold text-ink">
              What does this note concern?
            </legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {categories.map((item) => (
                <label
                  key={item.value}
                  className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border px-3 text-sm ${
                    category === item.value
                      ? "border-accent bg-accent-soft/55 text-ink"
                      : "border-line bg-canvas text-ink-soft hover:border-line-strong"
                  }`}
                >
                  <input
                    type="radio"
                    name="review-category"
                    value={item.value}
                    checked={category === item.value}
                    onChange={() => {
                      setCategory(item.value);
                      setStatus("idle");
                    }}
                    className="accent-[var(--accent)]"
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="mt-6 block">
            <span className="text-xs font-semibold text-ink">Review note</span>
            <span className="mt-1 block text-xs leading-5 text-ink-faint">
              State what you expected, what you observed, and what would make the
              evidence easier to evaluate.
            </span>
            <textarea
              ref={textareaRef}
              required
              maxLength={1200}
              value={notes}
              onChange={(event) => {
                setNotes(event.target.value);
                setStatus("idle");
              }}
              placeholder="Example: I expected the selected evidence node to explain why this result supports the cross-condition summary…"
              className="mt-3 min-h-36 w-full resize-y rounded-lg border border-line-strong bg-canvas px-3 py-3 text-sm leading-6 text-ink outline-none placeholder:text-ink-faint focus:border-accent"
            />
            <span className="mt-2 flex justify-between gap-4 text-xs text-ink-faint">
              <span>Required before export</span>
              <span className="numeric font-mono">{notes.length} / 1200</span>
            </span>
          </label>

          <label className="mt-5 flex cursor-pointer items-start gap-3 text-xs leading-5 text-ink-soft">
            <input
              type="checkbox"
              checked={includePage}
              onChange={(event) => setIncludePage(event.target.checked)}
              className="mt-1 accent-[var(--accent)]"
            />
            Include the current page path in the note. This is off by default and
            may include the selected gene or comparison parameters.
          </label>

          <div className="mt-7 flex flex-col gap-3 border-t border-line pt-5 sm:flex-row sm:flex-wrap">
            <button
              type="button"
              onClick={copyFeedback}
              disabled={!notes.trim()}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-canvas hover:bg-accent-dark disabled:cursor-not-allowed disabled:opacity-40"
            >
              {status === "copied" ? (
                <Check aria-hidden="true" size={17} />
              ) : (
                <Copy aria-hidden="true" size={17} />
              )}
              {status === "copied" ? "Copied" : "Copy review note"}
            </button>
            <button
              type="button"
              onClick={downloadFeedback}
              disabled={!notes.trim()}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-line-strong bg-canvas px-4 text-sm font-semibold text-ink hover:border-accent disabled:cursor-not-allowed disabled:opacity-40"
            >
              <DownloadSimple aria-hidden="true" size={17} />
              Download .md
            </button>
            {feedbackEmail ? (
              <button
                type="button"
                onClick={openEmailDraft}
                disabled={!notes.trim()}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-line-strong bg-canvas px-4 text-sm font-semibold text-ink hover:border-accent disabled:cursor-not-allowed disabled:opacity-40"
              >
                <EnvelopeSimple aria-hidden="true" size={17} />
                Open email draft
              </button>
            ) : null}
          </div>

          <p aria-live="polite" className="mt-3 min-h-5 text-xs text-ink-soft">
            {status === "copied"
              ? "Review note copied to the clipboard."
              : status === "downloaded"
                ? "Review note downloaded as Markdown."
                : status === "error"
                  ? "Add a review note, or use Download if clipboard access is unavailable."
                  : ""}
          </p>
        </div>
      </dialog>
    </>
  );
}
