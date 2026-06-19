import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { Badge, Button, Input, Modal, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type TipoLicencia = {
  id: string; codigo: string; nombre: string;
  base_legal: string | null; paga: boolean; computa_dias: boolean;
};

export function TiposLicenciaPage() {
  const [rows, setRows] = useState<TipoLicencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TipoLicencia | null>(null);
  const [form, setForm] = useState({ codigo: "", nombre: "", base_legal: "", paga: true, computa_dias: true });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<TipoLicencia[]>("/api/tipos-licencia");
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, []);

  function openCreate() {
    setEditing(null);
    setForm({ codigo: "", nombre: "", base_legal: "", paga: true, computa_dias: true });
    setError(null);
    setModalOpen(true);
  }

  function openEdit(t: TipoLicencia) {
    setEditing(t);
    setForm({
      codigo: t.codigo, nombre: t.nombre,
      base_legal: t.base_legal || "", paga: t.paga, computa_dias: t.computa_dias,
    });
    setError(null);
    setModalOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = {
        codigo: form.codigo, nombre: form.nombre,
        base_legal: form.base_legal || null, paga: form.paga, computa_dias: form.computa_dias,
      };
      if (editing) {
        await http.put(`/api/tipos-licencia/${editing.id}`, payload);
      } else {
        await http.post("/api/tipos-licencia", payload);
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
    if (!confirm("Eliminar este tipo de licencia?")) return;
    setDeleting(id);
    try {
      await http.delete(`/api/tipos-licencia/${id}`);
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
        title="Tipos de licencia"
        subtitle="Gestion de tipos de licencia disponibles"
        actions={
          <Button onClick={openCreate}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Nuevo tipo
          </Button>
        }
      />

      <Table>
        <THead>
          <tr>
            <TH>Codigo</TH>
            <TH>Nombre</TH>
            <TH>Base legal</TH>
            <TH>Paga</TH>
            <TH>Computa</TH>
            <TH className="w-32">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((t) => (
            <TR key={t.id}>
              <TD className="font-mono text-sm">{t.codigo}</TD>
              <TD className="font-semibold text-va-heading">{t.nombre}</TD>
              <TD className="text-va-muted text-sm">{t.base_legal || "—"}</TD>
              <TD><Badge variant={t.paga ? "green" : "gray"}>{t.paga ? "Si" : "No"}</Badge></TD>
              <TD><Badge variant={t.computa_dias ? "green" : "gray"}>{t.computa_dias ? "Si" : "No"}</Badge></TD>
              <TD>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(t)} className="text-sm text-accent-600 hover:underline">Editar</button>
                  <button
                    onClick={() => handleDelete(t.id)}
                    disabled={deleting === t.id}
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
        title={editing ? "Editar tipo de licencia" : "Nuevo tipo de licencia"}
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
          <Input
            label="Base legal"
            value={form.base_legal}
            onChange={(e) => setForm((f) => ({ ...f, base_legal: e.target.value }))}
            placeholder="Ej: Art. 32 CCT"
          />
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.paga}
                onChange={(e) => setForm((f) => ({ ...f, paga: e.target.checked }))}
                className="rounded border-va-border"
              />
              Paga
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.computa_dias}
                onChange={(e) => setForm((f) => ({ ...f, computa_dias: e.target.checked }))}
                className="rounded border-va-border"
              />
              Computa dias
            </label>
          </div>
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
