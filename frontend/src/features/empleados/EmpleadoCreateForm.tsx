import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { empleadosApi } from "@/api/empleados";
import { catalogosApi, type Area, type Categoria } from "@/api/catalogos";
import { Button, Input, Select, Card, CardBody, CardFooter, PageHeader } from "@/components/ui";

export function EmpleadoCreateForm() {
  const nav = useNavigate();
  const [areas, setAreas] = useState<Area[]>([]);
  const [cats, setCats] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(false);
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
    setLoading(true);
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
      setError(err?.response?.data?.error?.message ?? "Error al crear empleado");
    } finally {
      setLoading(false);
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <div>
      <PageHeader title="Nuevo empleado" subtitle="Complete los datos del empleado" />

      <form onSubmit={submit} className="max-w-3xl">
        <Card>
          <CardBody className="space-y-8">
            {/* Datos personales */}
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
                <Input label="CUIL" value={form.cuil} onChange={(e) => setF("cuil", e.target.value)} required placeholder="20-12345678-9" />
                <Input label="Fecha de nacimiento" type="date" value={form.fecha_nacimiento} onChange={(e) => setF("fecha_nacimiento", e.target.value)} />
                <Input label="Email" type="email" value={form.email} onChange={(e) => setF("email", e.target.value)} />
                <Input label="Telefono" value={form.telefono} onChange={(e) => setF("telefono", e.target.value)} />
              </div>
            </div>

            {/* Datos laborales */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
                  Datos laborales
                </h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Legajo" value={form.legajo} onChange={(e) => setF("legajo", e.target.value.replace(/\D/g, ""))} required placeholder="Solo numeros" inputMode="numeric" pattern="\d+" />
                <Input label="Fecha de ingreso" type="date" value={form.fecha_ingreso} onChange={(e) => setF("fecha_ingreso", e.target.value)} required />
                <Select label="Area" value={form.area_id} onChange={(e) => setF("area_id", e.target.value)} placeholder="Seleccione un area">
                  {areas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
                </Select>
                <Select label="Categoria" value={form.categoria_id} onChange={(e) => setF("categoria_id", e.target.value)} required placeholder="Seleccione una categoria">
                  {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </Select>
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
            <Button type="submit" loading={loading}>Guardar empleado</Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
