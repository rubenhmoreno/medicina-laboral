import { cn } from "@/lib/utils";

type BadgeVariant = "gray" | "blue" | "green" | "red" | "amber" | "navy" | "cyan";

const variantStyles: Record<BadgeVariant, string> = {
  gray: "bg-slate-100 text-slate-700",
  blue: "bg-blue-50 text-blue-700 border border-blue-200",
  green: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  red: "bg-red-50 text-red-700 border border-red-200",
  amber: "bg-amber-50 text-amber-700 border border-amber-200",
  navy: "bg-primary-50 text-primary-700 border border-primary-200",
  cyan: "bg-accent-50 text-accent-700 border border-accent-200",
};

const estadoVariant: Record<string, BadgeVariant> = {
  borrador: "gray",
  enviado: "blue",
  validado: "green",
  rechazado: "red",
  anulado: "amber",
  activo: "green",
  inactivo: "gray",
  admin: "navy",
  medico: "cyan",
  rrhh: "blue",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  className?: string;
}

export function Badge({ children, variant, size = "sm", className }: BadgeProps) {
  const text = typeof children === "string" ? children : "";
  const resolvedVariant = variant || estadoVariant[text.toLowerCase()] || "gray";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium capitalize",
        size === "sm" ? "px-2.5 py-0.5 text-xs" : "px-3 py-1 text-sm",
        variantStyles[resolvedVariant],
        className,
      )}
    >
      {children}
    </span>
  );
}
