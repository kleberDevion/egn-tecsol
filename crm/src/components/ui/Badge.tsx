import type { ReactNode } from "react";

type Tone = "blue" | "green" | "red" | "yellow" | "gray";

const tones: Record<Tone, string> = {
  blue: "bg-google-blue-bg text-google-blue-dark",
  green: "bg-google-green-bg text-google-green",
  red: "bg-google-red-bg text-google-red",
  yellow: "bg-yellow-50 text-google-yellow",
  gray: "bg-gray-100 text-ink-secondary",
};

export function Badge({ tone = "gray", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}
