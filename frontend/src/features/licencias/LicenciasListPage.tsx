import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { licenciasApi, type EstadoLicencia, type Licencia } from "@/api/licencias";
import { Badge, Button, PageHeader, Select, Input, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

const ESTADOS: EstadoLicencia[] = ["borrador", "enviado", "validado", "rechazado", "anulado"];

export function LicenciasListPage() {
  const [searchParams] = useSearchParams();
  const initialEstado = (searchParams.get("estado") ?? "") as EstadoLicencia | "";
  const initialVigente = searchParams.get("vigente") === "true";
  const [estado, setEstado] = useState<EstadoLicencia | "">(initialEstado);
  const [vigente, setVigente] = useState(initialVigente);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [rows, setRows] = useState<Licencia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    licenciasApi
      .list({
        estado: !vigente ? (estado || undefined) : undefined,
        vigente: vigente || undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
      })
      .then(setRows)
      .finally(() => setLoading(false));
  }, [estado, vigente, desde, hasta]);

  function clearFilters() {
    setEstado("");
    setVigente(false);
    setDesde("");
    setHasta("");
  }

  const hasFilters = estado || vigente || desde || hasta;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Licencias"
        subtitle={vigente ? "Licencias vigentes — pacientes cursando enfermedad" : "Gestion de licencias medicas"}
        actions={
          <Link to="/licencias/nueva">
            <Button>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Nueva licencia
            </Button>
          </Link>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-va-border bg-va-card p-4 shadow-sm">
        <label className="flex items-center gap-2 text-sm font-medium text-va-heading cursor-pointer">
          <input
            type="checkbox"
            checked={vigente}
            onChange={(e) => { setVigente(e.target.checked); if (e.target.checked) setEstado(""); }}
            className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
          />
          Solo vigentes (cursando hoy)
        </label>
        <Select
          label="Estado"
          value={estado}
          onChange={(e) => { setEstado(e.target.value as any); if (e.target.value) setVigente(false); }}
          placeholder="Todos los estados"
          className="w-48"
          disabled={vigente}
        >
          {ESTADOS.map((s) => (
            <option key={s} value={s} className="capitalize">{s}</option>
          ))}
        </Select>
        <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Limpiar filtros
          </Button>
        )}
      </div>

      <Table>
        <THead>
          <tr>
            <TH>Empleado</TH>
            <TH>Desde</TH>
            <TH>Hasta</TH>
            <TH>Dias</TH>
            <TH>Estado</TH>
            <TH className="text-right">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((l) => (
            <TR key={l.id}>
              <TD className="font-medium text-va-heading">{l.empleado_nombre ?? "—"}</TD>
              <TD>{l.fecha_desde}</TD>
              <TD>{l.fecha_hasta}</TD>
              <TD className="font-semibold text-va-heading">{l.dias_otorgados ?? l.dias_solicitados}</TD>
              <TD><Badge>{l.estado}</Badge></TD>
              <TD className="text-right">
                <Link to={`/licencias/${l.id}`}>
                  <Button variant="ghost" size="sm">Ver detalle</Button>
                </Link>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
