import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helper?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helper, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-va-heading">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "block w-full rounded-lg border bg-white px-3 py-2.5 text-sm shadow-sm transition-default",
            "placeholder:text-va-muted",
            "focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20",
            error
              ? "border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500/20"
              : "border-va-border",
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
        {helper && !error && <p className="text-xs text-va-muted">{helper}</p>}
      </div>
    );
  },
);

Input.displayName = "Input";
