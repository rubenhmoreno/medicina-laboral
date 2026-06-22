import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { catalogosApi, type TipoLicencia } from "@/api/catalogos";
import { empleadosApi, type Empleado } from "@/api/empleados";
import { licenciasApi } from "@/api/licencias";
import { adjuntosApi, validateFiles } from "@/api/adjuntos";
import { Button, Input, Select, Card, CardBody, CardFooter, PageHeader } from "@/components/ui";

export function LicenciaForm() {
  const nav = useNavigate();
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    empleado_id: "", tipo_licencia_id: "", diagnostico: "",
    fecha_desde: "", fecha_hasta: "",
    observaciones: "", certificante: "", matricula_certificante: "",
  });

  useEffect(() => {
    empleadosApi.list().then(setEmpleados);
    catalogosApi.tiposLicencia().then(setTipos);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const lic = await licenciasApi.create({
        empleado_id: form.empleado_id, tipo_licencia_id: form.tipo_licencia_id,
        diagnostico: form.diagnostico || null,
        fecha_desde: form.fecha_desde, fecha_hasta: form.fecha_hasta,
        observaciones: form.observaciones || null,
        certificante: form.certificante || null,
        matricula_certificante: form.matricula_certificante || null,
      });
      if (files.length) {
        const sizeErr = validateFiles(files);
        if (sizeErr) { setError(sizeErr); setLoading(false); return; }
        await adjuntosApi.uploadMany(files, { licencia_id: lic.id });
      }
      nav(`/licencias/${lic.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error al crear licencia");
    } finally {
      setLoading(false);
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <div>
      <PageHeader title="Nueva licencia" subtitle="Complete los datos de la licencia medica" />

      <form onSubmit={submit} className="max-w-3xl">
        <Card>
          <CardBody className="space-y-8">
            {/* Empleado */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Empleado</h3>
              </div>
              <Select
                label="Empleado"
                value={form.empleado_id}
                onChange={(e) => setF("empleado_id", e.target.value)}
                required
                placeholder="Seleccione un empleado"
              >
                {empleados.map((e) => (
                  <option key={e.id} value={e.id}>{e.apellido}, {e.nombre} ({e.legajo})</option>
                ))}
              </Select>
            </div>

            {/* Tipo y diagnostico */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Tipo y diagnostico</h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Select label="Tipo de licencia" value={form.tipo_licencia_id} onChange={(e) => setF("tipo_licencia_id", e.target.value)} required placeholder="Seleccione un tipo">
                  {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                </Select>
                <Input label="Diagnostico" value={form.diagnostico} onChange={(e) => setF("diagnostico", e.target.value)} placeholder="Ingrese el diagnostico..." />
              </div>
            </div>

            {/* Fechas */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Periodo</h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Fecha desde" type="date" value={form.fecha_desde} onChange={(e) => setF("fecha_desde", e.target.value)} required />
                <Input label="Fecha hasta" type="date" value={form.fecha_hasta} onChange={(e) => setF("fecha_hasta", e.target.value)} required />
              </div>
            </div>

            {/* Certificante */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Certificante</h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Nombre del certificante" value={form.certificante} onChange={(e) => setF("certificante", e.target.value)} />
                <Input label="Matricula del certificante" value={form.matricula_certificante} onChange={(e) => setF("matricula_certificante", e.target.value)} />
              </div>
            </div>

            {/* Observaciones y adjunto */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Observaciones y adjunto</h3>
              </div>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-va-heading">Observaciones</label>
                  <textarea
                    className="block w-full rounded-lg border border-va-border bg-white px-3 py-2.5 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                    rows={3}
                    value={form.observaciones}
                    onChange={(e) => setF("observaciones", e.target.value)}
                    placeholder="Notas adicionales..."
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-va-heading">Adjuntos (PDF/imagen, max 5 MB c/u)</label>
                  <input
                    type="file"
                    accept="application/pdf,image/*"
                    multiple
                    onChange={(e) => setFiles(e.target.files ? Array.from(e.target.files) : [])}
                    className="block w-full text-sm text-va-body file:mr-4 file:rounded-lg file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100"
                  />
                  {files.length > 0 && (
                    <p className="text-xs text-va-muted">{files.length} archivo(s) seleccionado(s)</p>
                  )}
                </div>
              </div>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </CardBody>

          <CardFooter className="flex justify-end gap-3">
            <Button type="button" variant="ghost" onClick={() => nav(-1)}>Cancelar</Button>
            <Button type="submit" loading={loading}>Guardar licencia</Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
