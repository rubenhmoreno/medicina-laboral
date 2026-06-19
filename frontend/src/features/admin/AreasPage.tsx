import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { Button, Input, Modal, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type Area = { id: string; nombre: string; parent_id: string | null };

export function AreasPage() {
  const [rows, setRows] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Area | null>(null);
  const [form, setForm] = useState({ nombre: "" });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Area[]>("/api/areas");
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, []);

  function openCreate() {
    setEditing(null);
    setForm({ nombre: "" });
    setError(null);
    setModalOpen(true);
  }

  function openEdit(a: Area) {
    setEditing(a);
    setForm({ nombre: a.nombre });
    setError(null);
    setModalOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (editing) {
        await http.put(`/api/areas/${editing.id}`, { nombre: form.nombre });
      } else {
        await http.post("/api/areas", { nombre: form.nombre });
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
    if (!confirm("Eliminar esta area?")) return;
    setDeleting(id);
    try {
      await http.delete(`/api/areas/${id}`);
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
        title="Areas"
        subtitle="Gestion de areas organizacionales"
        actions={
          <Button onClick={openCreate}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Nueva area
          </Button>
        }
      />

      <Table>
        <THead>
          <tr>
            <TH>Nombre</TH>
            <TH className="w-32">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((a) => (
            <TR key={a.id}>
              <TD className="font-semibold text-va-heading">{a.nombre}</TD>
              <TD>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(a)} className="text-sm text-accent-600 hover:underline">Editar</button>
                  <button
                    onClick={() => handleDelete(a.id)}
                    disabled={deleting === a.id}
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
        title={editing ? "Editar area" : "Nueva area"}
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
            label="Nombre"
            value={form.nombre}
            onChange={(e) => setForm({ nombre: e.target.value })}
            required
          />
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
