import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { Badge, Button, Input, Select, Modal, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type Usuario = {
  id: string;
  email: string;
  nombre: string | null;
  rol: "admin" | "medico" | "rrhh";
  matricula: string | null;
  activo: boolean;
  ultimo_login: string | null;
};

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "medico", label: "Medico" },
  { value: "rrhh", label: "RRHH" },
];

export function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", nombre: "", rol: "medico", matricula: "" });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Usuario[]>("/api/usuarios");
      setUsuarios(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await http.post("/api/usuarios", {
        email: form.email,
        password: form.password,
        nombre: form.nombre || null,
        rol: form.rol,
        matricula: form.matricula || null,
      });
      setModalOpen(false);
      setForm({ email: "", password: "", nombre: "", rol: "medico", matricula: "" });
      await reload();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error al crear usuario");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usuarios"
        subtitle="Gestion de usuarios del sistema"
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Nuevo usuario
          </Button>
        }
      />

      <Table>
        <THead>
          <tr>
            <TH>Usuario</TH>
            <TH>Nombre</TH>
            <TH>Rol</TH>
            <TH>Estado</TH>
            <TH>Ultimo acceso</TH>
          </tr>
        </THead>
        <TBody empty={!loading && usuarios.length === 0}>
          {usuarios.map((u) => (
            <TR key={u.id}>
              <TD className="font-semibold text-va-heading">{u.email}</TD>
              <TD>{u.nombre || "—"}</TD>
              <TD><Badge>{u.rol}</Badge></TD>
              <TD><Badge>{u.activo ? "activo" : "inactivo"}</Badge></TD>
              <TD className="text-va-muted text-xs">
                {u.ultimo_login ? new Date(u.ultimo_login).toLocaleString("es-AR") : "Nunca"}
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Nuevo usuario"
        size="md"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleCreate} loading={saving}>Crear usuario</Button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Usuario"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            required
            placeholder="nombre.usuario"
          />
          <Input
            label="Clave"
            type="password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            required
            placeholder="Clave de acceso"
          />
          <Input
            label="Nombre completo"
            value={form.nombre}
            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
            placeholder="Nombre y apellido"
          />
          <Select
            label="Rol"
            value={form.rol}
            onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}
            required
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </Select>
          {form.rol === "medico" && (
            <Input
              label="Matricula"
              value={form.matricula}
              onChange={(e) => setForm((f) => ({ ...f, matricula: e.target.value }))}
              placeholder="MN12345"
            />
          )}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </form>
      </Modal>
    </div>
  );
}
