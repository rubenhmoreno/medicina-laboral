import { useState } from "react";
import { reportesApi } from "@/api/reportes";

export function ReportesPage() {
  const [desde, setDesde] = useState("2026-01-01");
  const [hasta, setHasta] = useState("2026-12-31");
  const [rows, setRows] = useState<any[]>([]);
  const [tipo, setTipo] = useState<"por-area"|"por-categoria-diag"|"mensual">("por-area");

  async function cargar() {
    if (tipo === "por-area") setRows(await reportesApi.porArea(desde, hasta));
    if (tipo === "por-categoria-diag") setRows(await reportesApi.porCategoriaDiag(desde, hasta));
    if (tipo === "mensual") setRows(await reportesApi.mensual(desde, hasta));
  }

  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Reportes</h1>
      <div className="flex flex-wrap gap-2 items-end">
        <label className="text-sm">Desde<input type="date" className="block border rounded p-2" value={desde} onChange={(e) => setDesde(e.target.value)} /></label>
        <label className="text-sm">Hasta<input type="date" className="block border rounded p-2" value={hasta} onChange={(e) => setHasta(e.target.value)} /></label>
        <label className="text-sm">Reporte
          <select className="block border rounded p-2" value={tipo} onChange={(e) => setTipo(e.target.value as any)}>
            <option value="por-area">Por área</option>
            <option value="por-categoria-diag">Por categoría diagnóstica</option>
            <option value="mensual">Mensual</option>
          </select>
        </label>
        <button onClick={cargar} className="bg-slate-900 text-white px-3 py-2 rounded">Cargar</button>
        <button onClick={() => reportesApi.downloadCsv(tipo, desde, hasta)} className="border px-3 py-2 rounded">Exportar CSV</button>
      </div>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="bg-slate-100 text-left">
          <tr>{rows[0] ? Object.keys(rows[0]).map((k) => <th key={k} className="p-2">{k}</th>) : null}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t">
              {Object.values(r).map((v, j) => <td key={j} className="p-2">{String(v)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
