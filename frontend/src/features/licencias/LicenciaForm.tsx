// frontend/src/features/licencias/LicenciaForm.tsx
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { catalogosApi, type Diagnostico, type TipoLicencia } from "@/api/catalogos";
import { empleadosApi, type Empleado } from "@/api/empleados";
import { licenciasApi } from "@/api/licencias";
import { adjuntosApi } from "@/api/adjuntos";

export function LicenciaForm() {
  const nav = useNavigate();
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [diags, setDiags] = useState<Diagnostico[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    empleado_id: "", tipo_licencia_id: "", diagnostico_id: "",
    fecha_desde: "", fecha_hasta: "",
    observaciones: "", certificante: "", matricula_certificante: "",
  });

  useEffect(() => {
    empleadosApi.list().then(setEmpleados);
    catalogosApi.tiposLicencia().then(setTipos);
    catalogosApi.diagnosticos().then(setDiags);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const lic = await licenciasApi.create({
        empleado_id: form.empleado_id, tipo_licencia_id: form.tipo_licencia_id,
        diagnostico_id: form.diagnostico_id || null,
        fecha_desde: form.fecha_desde, fecha_hasta: form.fecha_hasta,
        observaciones: form.observaciones || null,
        certificante: form.certificante || null,
        matricula_certificante: form.matricula_certificante || null,
      });
      if (file) await adjuntosApi.upload(lic.id, file);
      nav(`/licencias/${lic.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error");
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) { setForm((p) => ({ ...p, [k]: v })); }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 max-w-2xl bg-white rounded shadow p-6">
      <h1 className="col-span-2 text-2xl font-semibold">Nueva licencia</h1>
      <label className="text-sm col-span-2">Empleado
        <select className="mt-1 w-full border rounded p-2" value={form.empleado_id}
                onChange={(e) => setF("empleado_id", e.target.value)} required>
          <option value="">—</option>
          {empleados.map((e) => <option key={e.id} value={e.id}>{e.apellido}, {e.nombre} ({e.legajo})</option>)}
        </select>
      </label>
      <label className="text-sm">Tipo
        <select className="mt-1 w-full border rounded p-2" value={form.tipo_licencia_id}
                onChange={(e) => setF("tipo_licencia_id", e.target.value)} required>
          <option value="">—</option>
          {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
        </select>
      </label>
      <label className="text-sm">Diagnóstico
        <select className="mt-1 w-full border rounded p-2" value={form.diagnostico_id}
                onChange={(e) => setF("diagnostico_id", e.target.value)}>
          <option value="">—</option>
          {diags.map((d) => <option key={d.id} value={d.id}>{d.descripcion}</option>)}
        </select>
      </label>
      <label className="text-sm">Desde
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_desde} onChange={(e) => setF("fecha_desde", e.target.value)} required />
      </label>
      <label className="text-sm">Hasta
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_hasta} onChange={(e) => setF("fecha_hasta", e.target.value)} required />
      </label>
      <label className="text-sm">Certificante
        <input className="mt-1 w-full border rounded p-2"
               value={form.certificante} onChange={(e) => setF("certificante", e.target.value)} />
      </label>
      <label className="text-sm">Matrícula certificante
        <input className="mt-1 w-full border rounded p-2"
               value={form.matricula_certificante} onChange={(e) => setF("matricula_certificante", e.target.value)} />
      </label>
      <label className="col-span-2 text-sm">Observaciones
        <textarea className="mt-1 w-full border rounded p-2" rows={3}
                  value={form.observaciones} onChange={(e) => setF("observaciones", e.target.value)} />
      </label>
      <label className="col-span-2 text-sm">Adjunto (PDF/imagen)
        <input type="file" accept="application/pdf,image/*"
               onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      {error && <p className="col-span-2 text-red-600 text-sm">{error}</p>}
      <div className="col-span-2 flex justify-end gap-2">
        <button type="button" onClick={() => nav(-1)} className="px-4 py-2">Cancelar</button>
        <button className="bg-slate-900 text-white px-4 py-2 rounded">Guardar</button>
      </div>
    </form>
  );
}
