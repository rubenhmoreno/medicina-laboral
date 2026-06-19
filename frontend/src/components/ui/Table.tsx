import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import { EmptyState } from "./EmptyState";

interface TableProps {
  children: ReactNode;
  className?: string;
}

export function Table({ children, className }: TableProps) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border border-va-border bg-va-card shadow-sm", className)}>
      <table className="min-w-full divide-y divide-va-border text-sm">
        {children}
      </table>
    </div>
  );
}

export function THead({ children, className }: TableProps) {
  return (
    <thead className={cn("bg-slate-50", className)}>
      {children}
    </thead>
  );
}

export function TBody({ children, className, empty }: TableProps & { empty?: boolean }) {
  if (empty) {
    return (
      <tbody>
        <tr>
          <td colSpan={100} className="py-12">
            <EmptyState message="No se encontraron registros" />
          </td>
        </tr>
      </tbody>
    );
  }
  return <tbody className={cn("divide-y divide-va-border", className)}>{children}</tbody>;
}

export function TH({ children, className }: TableProps) {
  return (
    <th className={cn("px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-va-muted", className)}>
      {children}
    </th>
  );
}

export function TD({ children, className }: TableProps) {
  return (
    <td className={cn("whitespace-nowrap px-4 py-3 text-va-body", className)}>
      {children}
    </td>
  );
}

export function TR({ children, className, onClick }: TableProps & { onClick?: () => void }) {
  return (
    <tr
      className={cn(
        "transition-default",
        onClick && "cursor-pointer hover:bg-accent-50/30",
        className,
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}
