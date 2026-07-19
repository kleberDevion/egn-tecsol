import type { ReactNode } from "react";

interface PageHeaderProps {
  action?: ReactNode;
}

export function PageHeader({ action }: PageHeaderProps) {
  if (!action) return null;
  return <div className="mb-4 flex justify-end">{action}</div>;
}
