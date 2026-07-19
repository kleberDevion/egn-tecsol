import type { ButtonHTMLAttributes } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  tone?: "default" | "danger";
}

export function IconButton({ label, tone = "default", className = "", children, ...rest }: IconButtonProps) {
  const toneClass =
    tone === "danger"
      ? "text-ink-faint hover:text-google-red hover:bg-google-red-bg"
      : "text-ink-faint hover:text-google-blue hover:bg-google-blue-bg";

  return (
    <button
      aria-label={label}
      title={label}
      className={`inline-flex items-center justify-center h-9 w-9 transition-colors cursor-pointer ${toneClass} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
