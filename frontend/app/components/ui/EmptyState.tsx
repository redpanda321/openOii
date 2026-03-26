import type { ReactNode } from "react";
import { Button } from "./Button";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center min-h-[300px]">
      {icon && (
        <div className="w-16 h-16 mb-4 rounded-full bg-base-200 flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-heading font-bold mb-2">{title}</h3>
      {description && (
        <p className="text-base-content/70 mb-4 max-w-sm">{description}</p>
      )}
      {action && (
        <Button variant="primary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
