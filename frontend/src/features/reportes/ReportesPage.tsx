import { useState } from "react";
import { reportesApi } from "@/api/reportes";
import { Button, Input, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type TipoReporte = "por-area" | "por-categoria-diag" | "mensual";

const REPORTES: { key: TipoReporte; label: string; desc: string; icon: React.ReactNode }[] = [
  {
    key: "por-area",
    label: "Por area",
    desc: "Dias de ausentismo agrupados por area",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008V7.5z" />
      </svg>
    ),
  },
  {
    key: "por-categoria-diag",
    label: "Por diagnostico",
    desc: "Licencias agrupadas por categoria diagnostica",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
  },
  {
    key: "mensual",
    label: "Mensual",
    desc: "Evolucion mensual de ausentismo",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
      </svg>
    ),
  },
];

export function ReportesPage() {
  const [desde, setDesde] = useState("2026-01-01");
  const [hasta, setHasta] = useState("2026-12-31");
  const [rows, setRows] = useState<any[]>([]);
  const [tipo, setTipo] = useState<TipoReporte>("por-area");
  const [loading, setLoading] = useState(false);

  async function cargar() {
    setLoading(true);
    try {
      if (tipo === "por-area") setRows(await reportesApi.porArea(desde, hasta));
      if (tipo === "por-categoria-diag") setRows(await reportesApi.porCategoriaDiag(desde, hasta));
      if (tipo === "mensual") setRows(await reportesApi.mensual(desde, hasta));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Reportes" subtitle="Reportes de ausentismo y licencias" />

      {/* Report type selection */}
      <div className="grid gap-4 sm:grid-cols-3">
        {REPORTES.map((r) => (
          <button
            key={r.key}
            onClick={() => setTipo(r.key)}
            className={`rounded-xl border p-5 text-left transition-default ${
              tipo === r.key
                ? "border-accent-400 bg-accent-50/50 ring-1 ring-accent-400 shadow-sm"
                : "border-va-border bg-va-card hover:border-accent-200 hover:shadow-sm"
            }`}
          >
            <div className={`mb-3 ${tipo === r.key ? "text-accent-600" : "text-va-muted"}`}>
              {r.icon}
            </div>
            <p className={`text-sm font-semibold ${tipo === r.key ? "text-primary-600" : "text-va-heading"}`}>
              {r.label}
            </p>
            <p className="mt-1 text-xs text-va-muted">{r.desc}</p>
          </button>
        ))}
      </div>

      {/* Date range + actions */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-va-border bg-va-card p-4 shadow-sm">
        <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        <Button onClick={cargar} loading={loading}>Generar reporte</Button>
        <Button
          variant="secondary"
          onClick={() => reportesApi.downloadCsv(tipo, desde, hasta)}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Exportar CSV
        </Button>
      </div>

      {/* Results */}
      {rows.length > 0 && (
        <Table>
          <THead>
            <tr>
              {Object.keys(rows[0]).map((k) => (
                <TH key={k}>{k.replace(/_/g, " ")}</TH>
              ))}
            </tr>
          </THead>
          <TBody>
            {rows.map((r, i) => (
              <TR key={i}>
                {Object.values(r).map((v, j) => (
                  <TD key={j} className={typeof v === "number" ? "font-mono text-right font-medium" : ""}>
                    {String(v)}
                  </TD>
                ))}
              </TR>
            ))}
          </TBody>
        </Table>
      )}
    </div>
  );
}
