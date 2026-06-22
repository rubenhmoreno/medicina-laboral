import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { empleadosApi, type Empleado } from "@/api/empleados";
import { adjuntosApi, validateFiles } from "@/api/adjuntos";
import { Button, Input, Select, Card, CardBody, CardFooter, PageHeader } from "@/components/ui";

type Usuario = { id: string; email: string; nombre: string | null; rol: string };

export function AtencionCreatePage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const isMedico = user?.rol === "medico";
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [medicos, setMedicos] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    empleado_id: "", medico_id: "", fecha_turno: "", motivo: "",
  });
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    empleadosApi.list().then(setEmpleados);
    if (!isMedico) {
      http.get<Usuario[]>("/api/usuarios").then((r) => {
        setMedicos(r.data.filter((u) => u.rol === "medico"));
      }).catch(() => {});
    }
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data: atencion } = await http.post("/api/atenciones", {
        empleado_id: form.empleado_id,
        medico_id: form.medico_id || null,
        fecha_turno: form.fecha_turno,
        motivo: form.motivo,
      });

      if (files.length) {
        const sizeErr = validateFiles(files);
        if (sizeErr) { setError(sizeErr); setLoading(false); return; }
        await adjuntosApi.uploadMany(files, { atencion_id: atencion.id });
      }

      nav(`/atenciones/${atencion.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error al crear turno");
    } finally {
      setLoading(false);
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <div>
      <PageHeader title="Nuevo turno" subtitle="Asignar un turno medico a un empleado" />

      <form onSubmit={submit} className="max-w-3xl">
        <Card>
          <CardBody className="space-y-6">
            <Select
              label="Empleado"
              value={form.empleado_id}
              onChange={(e) => setF("empleado_id", e.target.value)}
              required
              placeholder="Seleccione un empleado"
            >
              {empleados.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.apellido}, {emp.nombre} ({emp.legajo})
                </option>
              ))}
            </Select>

            {!isMedico && (
              <Select
                label="Medico asignado"
                value={form.medico_id}
                onChange={(e) => setF("medico_id", e.target.value)}
                placeholder="Sin asignar"
              >
                {medicos.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nombre || m.email}
                  </option>
                ))}
              </Select>
            )}

            <Input
              label="Fecha y hora del turno"
              type="datetime-local"
              value={form.fecha_turno}
              onChange={(e) => setF("fecha_turno", e.target.value)}
              required
            />

            <div>
              <label className="mb-1.5 block text-sm font-medium text-va-heading">Motivo</label>
              <textarea
                className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                rows={3}
                value={form.motivo}
                onChange={(e) => setF("motivo", e.target.value)}
                required
                placeholder="Motivo de la consulta..."
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-va-heading">Adjuntos (opcional, max 5 MB c/u)</label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.webp"
                multiple
                onChange={(e) => setFiles(e.target.files ? Array.from(e.target.files) : [])}
                className="block w-full text-sm text-va-body file:mr-3 file:rounded-lg file:border-0 file:bg-accent-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-accent-700 hover:file:bg-accent-100"
              />
              {files.length > 0 && (
                <p className="mt-1 text-xs text-va-muted">{files.length} archivo(s) seleccionado(s)</p>
              )}
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </CardBody>

          <CardFooter className="flex justify-end gap-3">
            <Button type="button" variant="ghost" onClick={() => nav(-1)}>Cancelar</Button>
            <Button type="submit" loading={loading}>Crear turno</Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
