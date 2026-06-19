import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import {
  Badge, Button, Card, CardBody, Input, Modal, PageHeader, Select,
  Table, THead, TBody, TH, TD, TR,
} from "@/components/ui";

type Estudio = {
  id: string; nombre: string; codigo: string | null;
  tipo: string; categoria: string | null; activo: boolean;
};

const TIPO_COLORS: Record<string, "blue" | "green" | "gray"> = {
  laboratorio: "blue",
  imagen: "green",
  otro: "gray",
};

export function EstudiosCatalogoPage() {
  const [rows, setRows] = useState<Estudio[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterTipo, setFilterTipo] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ nombre: "", codigo: "", tipo: "laboratorio", categoria: "", activo: true });

  async function reload() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterTipo) params.tipo = filterTipo;
      const { data } = await http.get<Estudio[]>("/api/estudios-catalogo", { params });
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [filterTipo]);

  function openNew() {
    setEditId(null);
    setForm({ nombre: "", codigo: "", tipo: "laboratorio", categoria: "", activo: true });
    setModalOpen(true);
  }

  function openEdit(est: Estudio) {
    setEditId(est.id);
    setForm({
      nombre: est.nombre,
      codigo: est.codigo ?? "",
      tipo: est.tipo,
      categoria: est.categoria ?? "",
      activo: est.activo,
    });
    setModalOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const body = {
        nombre: form.nombre,
        codigo: form.codigo || null,
        tipo: form.tipo,
        categoria: form.categoria || null,
        activo: form.activo,
      };
      if (editId) {
        await http.put(`/api/estudios-catalogo/${editId}`, body);
      } else {
        await http.post("/api/estudios-catalogo", body);
      }
      setModalOpen(false);
      await reload();
    } finally {
      setSaving(false);
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Catalogo de estudios"
        subtitle="Estudios de laboratorio, imagen y otros"
        actions={<Button onClick={openNew}>Nuevo estudio</Button>}
      />

      <div className="flex flex-wrap gap-4">
        <Select label="Tipo" value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)} placeholder="Todos">
          <option value="laboratorio">Laboratorio</option>
          <option value="imagen">Imagen</option>
          <option value="otro">Otro</option>
        </Select>
        {filterTipo && (
          <div className="flex items-end">
            <Button variant="ghost" onClick={() => setFilterTipo("")}>Limpiar</Button>
          </div>
        )}
      </div>

      <Table>
        <THead>
          <tr>
            <TH>Nombre</TH>
            <TH>Codigo</TH>
            <TH>Tipo</TH>
            <TH>Categoria</TH>
            <TH>Estado</TH>
            <TH className="w-24">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((est) => (
            <TR key={est.id}>
              <TD className="font-semibold text-va-heading">{est.nombre}</TD>
              <TD className="text-va-muted font-mono text-xs">{est.codigo ?? "—"}</TD>
              <TD><Badge variant={TIPO_COLORS[est.tipo] ?? "gray"}>{est.tipo}</Badge></TD>
              <TD>{est.categoria ?? "—"}</TD>
              <TD><Badge variant={est.activo ? "green" : "gray"}>{est.activo ? "Activo" : "Inactivo"}</Badge></TD>
              <TD>
                <button onClick={() => openEdit(est)} className="text-sm text-accent-600 hover:underline">Editar</button>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editId ? "Editar estudio" : "Nuevo estudio"}
        size="md"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit} loading={saving}>Guardar</Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Nombre" value={form.nombre} onChange={(e) => setF("nombre", e.target.value)} required />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Codigo" value={form.codigo} onChange={(e) => setF("codigo", e.target.value)} placeholder="Opcional" />
            <Select label="Tipo" value={form.tipo} onChange={(e) => setF("tipo", e.target.value)}>
              <option value="laboratorio">Laboratorio</option>
              <option value="imagen">Imagen</option>
              <option value="otro">Otro</option>
            </Select>
          </div>
          <Input label="Categoria" value={form.categoria} onChange={(e) => setF("categoria", e.target.value)} placeholder="Opcional" />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.activo}
              onChange={(e) => setF("activo", e.target.checked)}
              className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
            />
            <span className="text-va-heading">Activo</span>
          </label>
        </form>
      </Modal>
    </div>
  );
}
