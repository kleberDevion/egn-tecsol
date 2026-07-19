import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 border border-dashed border-border bg-white px-6 py-16 text-center">
      <div className="text-ink-faint">{icon}</div>
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-secondary">{description}</p>}
      {action}
    </div>
  );
}
