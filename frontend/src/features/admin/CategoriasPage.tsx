import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { Badge, Button, Input, Modal, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type Categoria = { id: string; codigo: string; nombre: string; activa: boolean };

export function CategoriasPage() {
  const [rows, setRows] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Categoria | null>(null);
  const [form, setForm] = useState({ codigo: "", nombre: "", activa: true });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Categoria[]>("/api/categorias");
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, []);

  function openCreate() {
    setEditing(null);
    setForm({ codigo: "", nombre: "", activa: true });
    setError(null);
    setModalOpen(true);
  }

  function openEdit(c: Categoria) {
    setEditing(c);
    setForm({ codigo: c.codigo, nombre: c.nombre, activa: c.activa });
    setError(null);
    setModalOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (editing) {
        await http.put(`/api/categorias/${editing.id}`, form);
      } else {
        await http.post("/api/categorias", { codigo: form.codigo, nombre: form.nombre });
      }
      setModalOpen(false);
      await reload();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Eliminar esta categoria?")) return;
    setDeleting(id);
    try {
      await http.delete(`/api/categorias/${id}`);
      await reload();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message ?? "Error al eliminar");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Categorias laborales"
        subtitle="Gestion de categorias de empleados"
        actions={
          <Button onClick={openCreate}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Nueva categoria
          </Button>
        }
      />

      <Table>
        <THead>
          <tr>
            <TH>Codigo</TH>
            <TH>Nombre</TH>
            <TH>Estado</TH>
            <TH className="w-32">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((c) => (
            <TR key={c.id}>
              <TD className="font-mono text-sm">{c.codigo}</TD>
              <TD className="font-semibold text-va-heading">{c.nombre}</TD>
              <TD><Badge>{c.activa ? "activa" : "inactiva"}</Badge></TD>
              <TD>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(c)} className="text-sm text-accent-600 hover:underline">Editar</button>
                  <button
                    onClick={() => handleDelete(c.id)}
                    disabled={deleting === c.id}
                    className="text-sm text-red-600 hover:underline disabled:opacity-50"
                  >
                    Eliminar
                  </button>
                </div>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar categoria" : "Nueva categoria"}
        size="md"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit} loading={saving}>{editing ? "Guardar" : "Crear"}</Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Codigo"
            value={form.codigo}
            onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value }))}
            required
          />
          <Input
            label="Nombre"
            value={form.nombre}
            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
            required
          />
          {editing && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.activa}
                onChange={(e) => setForm((f) => ({ ...f, activa: e.target.checked }))}
                className="rounded border-va-border"
              />
              Activa
            </label>
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
