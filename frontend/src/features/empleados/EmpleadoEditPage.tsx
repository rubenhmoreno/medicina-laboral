import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { http } from "@/api/http";
import { catalogosApi, type Area, type Categoria } from "@/api/catalogos";
import { Button, Input, Select, Card, CardBody, CardFooter, PageHeader } from "@/components/ui";

type Empleado = {
  id: string; legajo: string; cuil: string;
  nombre: string; apellido: string;
  fecha_nacimiento: string | null; fecha_ingreso: string;
  area_id: string | null; categoria_id: string;
  supervisor_id: string | null;
  email: string | null; telefono: string | null; activo: boolean;
};

export function EmpleadoEditPage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [areas, setAreas] = useState<Area[]>([]);
  const [cats, setCats] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nombre: "", apellido: "", area_id: "", categoria_id: "",
    email: "", telefono: "", activo: true,
  });
  const [empleado, setEmpleado] = useState<Empleado | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      http.get<Empleado>(`/api/empleados/${id}`).then((r) => r.data),
      catalogosApi.areas(),
      catalogosApi.categorias(),
    ]).then(([emp, a, c]) => {
      setEmpleado(emp);
      setAreas(a);
      setCats(c);
      setForm({
        nombre: emp.nombre, apellido: emp.apellido,
        area_id: emp.area_id || "", categoria_id: emp.categoria_id,
        email: emp.email || "", telefono: emp.telefono || "",
        activo: emp.activo,
      });
      setLoading(false);
    });
  }, [id]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await http.put(`/api/empleados/${id}`, {
        nombre: form.nombre, apellido: form.apellido,
        area_id: form.area_id || null, categoria_id: form.categoria_id,
        email: form.email || null, telefono: form.telefono || null,
        activo: form.activo,
      });
      nav("/empleados");
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error al actualizar");
    } finally {
      setSaving(false);
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  if (loading) return <div className="p-6 text-va-muted">Cargando...</div>;
  if (!empleado) return <div className="p-6 text-red-600">Empleado no encontrado</div>;

  return (
    <div>
      <PageHeader
        title={`Editar: ${empleado.apellido}, ${empleado.nombre}`}
        subtitle={`Legajo ${empleado.legajo} - CUIL ${empleado.cuil}`}
      />

      <form onSubmit={submit} className="max-w-3xl">
        <Card>
          <CardBody className="space-y-8">
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
                  Datos personales
                </h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Apellido" value={form.apellido} onChange={(e) => setF("apellido", e.target.value)} required />
                <Input label="Nombre" value={form.nombre} onChange={(e) => setF("nombre", e.target.value)} required />
                <Input label="Email" type="email" value={form.email} onChange={(e) => setF("email", e.target.value)} />
                <Input label="Telefono" value={form.telefono} onChange={(e) => setF("telefono", e.target.value)} />
              </div>
            </div>

            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
                  Datos laborales
                </h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Select label="Area" value={form.area_id} onChange={(e) => setF("area_id", e.target.value)} placeholder="Seleccione un area">
                  {areas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
                </Select>
                <Select label="Categoria" value={form.categoria_id} onChange={(e) => setF("categoria_id", e.target.value)} required placeholder="Seleccione una categoria">
                  {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </Select>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.activo}
                    onChange={(e) => setF("activo", e.target.checked)}
                    className="rounded border-va-border"
                  />
                  Empleado activo
                </label>
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
            <Button type="submit" loading={saving}>Guardar cambios</Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
