import type { Severity } from "../types/issue";

const STYLE: Record<Severity, string> = {
  low:      "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  medium:   "bg-amber-500/10 text-amber-300 border-amber-500/30",
  high:     "bg-orange-500/10 text-orange-300 border-orange-500/30",
  critical: "bg-rose-500/10 text-rose-300 border-rose-500/30",
};

const ICON: Record<Severity, string> = {
  low:      "○",
  medium:   "◐",
  high:     "●",
  critical: "⬤",
};

interface Props {
  severity: Severity;
  confidence?: number;
  size?: "sm" | "md";
}

export default function SeverityBadge({ severity, confidence, size = "md" }: Props) {
  const s = severity.toLowerCase() as Severity;
  const px = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-semibold ${STYLE[s]} ${px}`}>
      <span aria-hidden>{ICON[s] ?? "●"}</span>
      {s.toUpperCase()}
      {confidence !== undefined && (
        <span className="opacity-70 font-normal">({Math.round(confidence * 100)}%)</span>
      )}
    </span>
  );
}
