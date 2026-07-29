import type { Condition } from "@/lib/types";

export const conditionLabel: Record<Condition, string> = {
  Rest: "Rest",
  Stim8hr: "8 h stimulation",
  Stim48hr: "48 h stimulation",
};

export const stageLabel: Record<string, string> = {
  all_screen_rows: "All screen rows",
  on_target_significant: "On-target significant",
  negative_on_target_effect: "Negative on-target effect",
  off_target_flag_false: "No source off-target flag",
  n_cells_target_at_least_100: "At least 100 targeted cells",
  cross_donor_metric_present_and_positive: "Positive donor concordance",
  cross_guide_metric_present_and_positive: "Positive guide concordance",
};

export function formatScore(value: number, digits = 3) {
  return value.toFixed(digits);
}

export function formatInteger(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatSigned(value: number, digits = 3) {
  const formatted = Math.abs(value).toFixed(digits);
  return value > 0 ? `+${formatted}` : value < 0 ? `−${formatted}` : formatted;
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

export function sentenceCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
