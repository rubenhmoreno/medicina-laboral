import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { empleadosApi } from "@/api/empleados";
import { catalogosApi, type Area, type Categoria } from "@/api/catalogos";

export function EmpleadoCreateForm() {
  const nav = useNavigate();
  const [areas, setAreas] = useState<Area[]>([]);
  const [cats, setCats] = useState<Categoria[]>([]);
  const [form, setForm] = useState({
    legajo: "", cuil: "", nombre: "", apellido: "",
    fecha_nacimiento: "", fecha_ingreso: "",
    area_id: "", categoria_id: "", supervisor_id: "",
    email: "", telefono: "",
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    catalogosApi.areas().then(setAreas);
    catalogosApi.categorias().then(setCats);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await empleadosApi.create({
        legajo: form.legajo, cuil: form.cuil,
        nombre: form.nombre, apellido: form.apellido,
        fecha_nacimiento: form.fecha_nacimiento || null,
        fecha_ingreso: form.fecha_ingreso,
        area_id: form.area_id || null,
        categoria_id: form.categoria_id,
        supervisor_id: form.supervisor_id || null,
        email: form.email || null, telefono: form.telefono || null,
      });
      nav("/empleados");
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error");
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 max-w-2xl bg-white rounded shadow p-6">
      <h1 className="col-span-2 text-2xl font-semibold">Nuevo empleado</h1>
      {(["legajo","cuil","apellido","nombre","email","telefono"] as const).map((k) => (
        <label key={k} className="text-sm">
          {k}
          <input className="mt-1 w-full border rounded p-2"
                 value={form[k]} onChange={(e) => setF(k, e.target.value)} required={["legajo","cuil","apellido","nombre"].includes(k)} />
        </label>
      ))}
      <label className="text-sm">Fecha de ingreso
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_ingreso} onChange={(e) => setF("fecha_ingreso", e.target.value)} required />
      </label>
      <label className="text-sm">Fecha de nacimiento
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_nacimiento} onChange={(e) => setF("fecha_nacimiento", e.target.value)} />
      </label>
      <label className="text-sm">Área
        <select className="mt-1 w-full border rounded p-2"
                value={form.area_id} onChange={(e) => setF("area_id", e.target.value)}>
          <option value="">—</option>
          {areas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
        </select>
      </label>
      <label className="text-sm">Categoría
        <select className="mt-1 w-full border rounded p-2"
                value={form.categoria_id} onChange={(e) => setF("categoria_id", e.target.value)} required>
          <option value="">—</option>
          {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select>
      </label>
      {error && <p className="col-span-2 text-red-600 text-sm">{error}</p>}
      <div className="col-span-2 flex justify-end gap-2">
        <button type="button" onClick={() => nav(-1)} className="px-4 py-2">Cancelar</button>
        <button className="bg-slate-900 text-white px-4 py-2 rounded">Guardar</button>
      </div>
    </form>
  );
}
