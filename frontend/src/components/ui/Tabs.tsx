import { cn } from "@/lib/utils";

type Tab = {
  key: string;
  label: string;
};

type TabsProps = {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
};

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="border-b border-va-border">
      <nav className="-mb-px flex gap-1 overflow-x-auto" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => onChange(tab.key)}
            className={cn(
              "whitespace-nowrap px-4 py-2.5 text-sm font-medium transition-default rounded-t-lg",
              active === tab.key
                ? "border-b-2 border-accent-500 text-accent-600 bg-accent-50/50"
                : "text-va-muted hover:text-va-heading hover:bg-slate-50",
            )}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
