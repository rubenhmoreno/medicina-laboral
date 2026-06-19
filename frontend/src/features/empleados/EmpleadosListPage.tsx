import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { empleadosApi, type Empleado } from "@/api/empleados";

export function EmpleadosListPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Empleado[]>([]);
  useEffect(() => {
    const t = setTimeout(() => empleadosApi.list(q).then(setRows), 250);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Empleados</h1>
        <Link to="/empleados/nuevo" className="bg-slate-900 text-white px-3 py-2 rounded">Nuevo</Link>
      </header>
      <input className="border rounded p-2 w-full max-w-md"
             placeholder="Buscar por legajo, CUIL o nombre…"
             value={q} onChange={(e) => setQ(e.target.value)} />
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="text-left bg-slate-100">
          <tr>
            <th className="p-2">Legajo</th><th className="p-2">Apellido y nombre</th>
            <th className="p-2">CUIL</th><th className="p-2">Categoría</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((e) => (
            <tr key={e.id} className="border-t">
              <td className="p-2">{e.legajo}</td>
              <td className="p-2">{e.apellido}, {e.nombre}</td>
              <td className="p-2">{e.cuil}</td>
              <td className="p-2">{e.categoria_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
