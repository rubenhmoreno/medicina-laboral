// frontend/src/features/licencias/LicenciasListPage.tsx
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { licenciasApi, type EstadoLicencia, type Licencia } from "@/api/licencias";

const ESTADOS: EstadoLicencia[] = ["borrador","enviado","validado","rechazado","anulado"];

export function LicenciasListPage() {
  const [estado, setEstado] = useState<EstadoLicencia | "">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [rows, setRows] = useState<Licencia[]>([]);

  useEffect(() => {
    licenciasApi.list({
      estado: estado || undefined,
      desde: desde || undefined,
      hasta: hasta || undefined,
    }).then(setRows);
  }, [estado, desde, hasta]);

  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Licencias</h1>
        <Link to="/licencias/nueva" className="bg-slate-900 text-white px-3 py-2 rounded">Nueva</Link>
      </header>
      <div className="flex flex-wrap gap-2">
        <select className="border rounded p-2" value={estado} onChange={(e) => setEstado(e.target.value as any)}>
          <option value="">(estado)</option>
          {ESTADOS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" className="border rounded p-2" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <input type="date" className="border rounded p-2" value={hasta} onChange={(e) => setHasta(e.target.value)} />
      </div>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="text-left bg-slate-100">
          <tr><th className="p-2">Desde</th><th className="p-2">Hasta</th><th className="p-2">Días</th><th className="p-2">Estado</th><th className="p-2"></th></tr>
        </thead>
        <tbody>
          {rows.map((l) => (
            <tr key={l.id} className="border-t">
              <td className="p-2">{l.fecha_desde}</td>
              <td className="p-2">{l.fecha_hasta}</td>
              <td className="p-2">{l.dias_otorgados ?? l.dias_solicitados}</td>
              <td className="p-2"><span className="px-2 py-1 rounded bg-slate-200">{l.estado}</span></td>
              <td className="p-2"><Link to={`/licencias/${l.id}`} className="underline">Detalle</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
