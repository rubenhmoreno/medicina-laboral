import { useEffect, useMemo, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Badge, Button, Card, CardBody, Input, Modal, Select } from "@/components/ui";

type EstudioCatalogo = { id: string; nombre: string; codigo: string | null; tipo: string; categoria: string | null };

type ItemPedido = { id: string; descripcion: string; codigo: string | null; orden: number };

type Pedido = {
  id: string; atencion_id: string; medico_id: string;
  tipo: string; diagnostico: string | null; indicaciones: string | null;
  created_at: string; items: ItemPedido[];
};

const TIPO_COLORS: Record<string, "blue" | "green" | "amber" | "gray"> = {
  laboratorio: "blue",
  imagen: "green",
  interconsulta: "amber",
  otro: "gray",
};

export function PedidosCard({ atencionId }: { atencionId: string }) {
  const { user } = useAuth();
  const canEdit = user && (user.rol === "admin" || user.rol === "medico");
  const [rows, setRows] = useState<Pedido[]>([]);
  const [catalogo, setCatalogo] = useState<EstudioCatalogo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const [tipo, setTipo] = useState("laboratorio");
  const [diagnostico, setDiagnostico] = useState("");
  const [indicaciones, setIndicaciones] = useState("");
  const [selectedEstudios, setSelectedEstudios] = useState<Set<string>>(new Set());
  const [textoLibre, setTextoLibre] = useState("");

  // Estudios selector modal
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [searchCat, setSearchCat] = useState("");
  const [filterCategoria, setFilterCategoria] = useState("__all__");

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Pedido[]>(`/api/pedidos/by-atencion/${atencionId}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
    http.get<EstudioCatalogo[]>("/api/estudios-catalogo", { params: { activo: true } })
      .then((r) => setCatalogo(r.data)).catch(() => {});
  }, [atencionId]);

  const filteredCatalogo = useMemo(() =>
    catalogo.filter(
      (e) => e.tipo === tipo && (
        !searchCat ||
        e.nombre.toLowerCase().includes(searchCat.toLowerCase()) ||
        (e.codigo && e.codigo.toLowerCase().includes(searchCat.toLowerCase()))
      ) && (
        filterCategoria === "__all__" || e.categoria === filterCategoria
      ),
    ),
    [catalogo, tipo, searchCat, filterCategoria],
  );

  // Group filtered catalog by categoria
  const groupedCatalogo = useMemo(() => {
    const groups: Record<string, EstudioCatalogo[]> = {};
    for (const est of filteredCatalogo) {
      const cat = est.categoria || "General";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(est);
    }
    // Sort categories alphabetically, but "General" last
    const sorted = Object.keys(groups).sort((a, b) => {
      if (a === "General") return 1;
      if (b === "General") return -1;
      return a.localeCompare(b);
    });
    return sorted.map((cat) => ({ categoria: cat, estudios: groups[cat] }));
  }, [filteredCatalogo]);

  // All unique categories for the current tipo
  const categorias = useMemo(() => {
    const cats = new Set<string>();
    for (const est of catalogo) {
      if (est.tipo === tipo && est.categoria) cats.add(est.categoria);
    }
    return Array.from(cats).sort();
  }, [catalogo, tipo]);

  function toggleEstudio(id: string) {
    setSelectedEstudios((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleCategoria(catEstudios: EstudioCatalogo[]) {
    setSelectedEstudios((prev) => {
      const next = new Set(prev);
      const allSelected = catEstudios.every((e) => next.has(e.id));
      if (allSelected) {
        catEstudios.forEach((e) => next.delete(e.id));
      } else {
        catEstudios.forEach((e) => next.add(e.id));
      }
      return next;
    });
  }

  function resetForm() {
    setTipo("laboratorio");
    setDiagnostico("");
    setIndicaciones("");
    setSelectedEstudios(new Set());
    setTextoLibre("");
    setSearchCat("");
    setFilterCategoria("__all__");
    setShowForm(false);
  }

  function openSelector() {
    setSearchCat("");
    setFilterCategoria("__all__");
    setSelectorOpen(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const items: { descripcion: string; codigo: string | null }[] = [];
    for (const estId of selectedEstudios) {
      const est = catalogo.find((c) => c.id === estId);
      if (est) items.push({ descripcion: est.nombre, codigo: est.codigo });
    }
    if (textoLibre.trim()) {
      for (const line of textoLibre.split("\n")) {
        const trimmed = line.trim();
        if (trimmed) items.push({ descripcion: trimmed, codigo: null });
      }
    }
    if (items.length === 0) return;
    setSaving(true);
    try {
      await http.post("/api/pedidos", {
        atencion_id: atencionId,
        tipo,
        diagnostico: diagnostico || null,
        indicaciones: indicaciones || null,
        items,
      });
      resetForm();
      await reload();
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="text-sm text-va-muted py-4">Cargando pedidos...</div>;

  // Names of selected estudios for display
  const selectedNames = Array.from(selectedEstudios).map((id) => {
    const est = catalogo.find((c) => c.id === id);
    return est?.nombre ?? id;
  });

  return (
    <div className="space-y-4">
      {canEdit && !showForm && (
        <div className="flex justify-end">
          <Button onClick={() => setShowForm(true)}>Nuevo pedido</Button>
        </div>
      )}

      {showForm && (
        <Card>
          <CardBody>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading mb-4">Nuevo pedido medico</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Select label="Tipo" value={tipo} onChange={(e) => { setTipo(e.target.value); setSelectedEstudios(new Set()); }}>
                  <option value="laboratorio">Laboratorio</option>
                  <option value="imagen">Imagen</option>
                  <option value="interconsulta">Interconsulta</option>
                  <option value="otro">Otro</option>
                </Select>
                <Input label="Diagnostico" value={diagnostico} onChange={(e) => setDiagnostico(e.target.value)} placeholder="Diagnostico..." />
                <Input label="Indicaciones" value={indicaciones} onChange={(e) => setIndicaciones(e.target.value)} placeholder="Indicaciones..." />
              </div>

              {(tipo === "laboratorio" || tipo === "imagen") && (
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Estudios del catalogo</label>
                  <button
                    type="button"
                    onClick={openSelector}
                    className="w-full rounded-lg border border-va-border bg-va-card px-4 py-3 text-left text-sm shadow-sm transition-default hover:border-accent-400 focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  >
                    {selectedEstudios.size === 0 ? (
                      <span className="text-va-muted">Seleccionar estudios...</span>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedNames.map((name, i) => (
                          <span key={i} className="inline-flex items-center rounded-md bg-accent-50 px-2 py-0.5 text-xs font-medium text-accent-700 ring-1 ring-inset ring-accent-200">
                            {name}
                          </span>
                        ))}
                      </div>
                    )}
                  </button>
                  <p className="mt-1 text-xs text-va-muted">{selectedEstudios.size} estudio(s) seleccionado(s)</p>
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Estudios adicionales (texto libre, uno por linea)</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={3} value={textoLibre} onChange={(e) => setTextoLibre(e.target.value)}
                  placeholder="Ej: Hemograma completo&#10;Glucemia en ayunas"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" loading={saving}>Crear pedido</Button>
                <Button type="button" variant="ghost" onClick={resetForm}>Cancelar</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {rows.length === 0 && !showForm && (
        <Card>
          <CardBody className="text-center py-8">
            <p className="text-sm text-va-muted">No hay pedidos registrados</p>
          </CardBody>
        </Card>
      )}

      {rows.map((ped) => (
        <Card key={ped.id}>
          <CardBody className="space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-va-heading">Pedido</h4>
                <Badge variant={TIPO_COLORS[ped.tipo] ?? "gray"}>{ped.tipo}</Badge>
              </div>
              <span className="text-xs text-va-muted">{new Date(ped.created_at).toLocaleString("es-AR")}</span>
            </div>
            {ped.diagnostico && (
              <p className="text-sm"><span className="font-medium text-va-heading">Diagnostico: </span><span className="text-va-body">{ped.diagnostico}</span></p>
            )}
            {ped.indicaciones && (
              <p className="text-sm"><span className="font-medium text-va-heading">Indicaciones: </span><span className="text-va-body">{ped.indicaciones}</span></p>
            )}
            <ul className="list-disc list-inside text-sm text-va-body space-y-1">
              {ped.items.map((it) => (
                <li key={it.id}>
                  {it.descripcion}
                  {it.codigo && <span className="text-xs text-va-muted ml-1">({it.codigo})</span>}
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      ))}

      {/* Estudios Selector Modal */}
      <Modal
        open={selectorOpen}
        onClose={() => setSelectorOpen(false)}
        title={`Seleccionar estudios — ${tipo === "laboratorio" ? "Laboratorio" : "Imagen"}`}
        size="2xl"
        actions={
          <>
            <span className="mr-auto text-sm text-va-muted">{selectedEstudios.size} seleccionado(s)</span>
            <Button variant="secondary" onClick={() => setSelectorOpen(false)}>Cerrar</Button>
          </>
        }
      >
        <div className="space-y-4">
          {/* Search and filter */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-va-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <input
                className="block w-full rounded-lg border border-va-border bg-va-card py-2.5 pl-10 pr-3 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                placeholder="Buscar estudio por nombre o codigo..."
                value={searchCat}
                onChange={(e) => setSearchCat(e.target.value)}
                autoFocus
              />
            </div>
            {categorias.length > 0 && (
              <select
                className="rounded-lg border border-va-border bg-va-card px-3 py-2.5 text-sm shadow-sm"
                value={filterCategoria}
                onChange={(e) => setFilterCategoria(e.target.value)}
              >
                <option value="__all__">Todas las categorias</option>
                {categorias.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            )}
          </div>

          {/* Estudios grouped by category */}
          <div className="max-h-[28rem] overflow-y-auto rounded-lg border border-va-border bg-white">
            {groupedCatalogo.length === 0 && (
              <p className="py-8 text-center text-sm text-va-muted">Sin resultados para la busqueda</p>
            )}
            {groupedCatalogo.map((group) => {
              const allSelected = group.estudios.every((e) => selectedEstudios.has(e.id));
              const someSelected = !allSelected && group.estudios.some((e) => selectedEstudios.has(e.id));
              return (
                <div key={group.categoria}>
                  {/* Category header */}
                  <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-va-border bg-slate-50 px-4 py-2.5">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => { if (el) el.indeterminate = someSelected; }}
                      onChange={() => toggleCategoria(group.estudios)}
                      className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
                    />
                    <span className="text-sm font-semibold text-va-heading uppercase tracking-wider">{group.categoria}</span>
                    <span className="text-xs text-va-muted">
                      ({group.estudios.filter((e) => selectedEstudios.has(e.id)).length}/{group.estudios.length})
                    </span>
                  </div>
                  {/* Items */}
                  <div className="grid grid-cols-1 sm:grid-cols-2">
                    {group.estudios.map((est) => (
                      <label
                        key={est.id}
                        className={`flex items-center gap-3 border-b border-va-border/50 px-4 py-2.5 cursor-pointer transition-colors ${
                          selectedEstudios.has(est.id) ? "bg-accent-50/60" : "hover:bg-slate-50"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedEstudios.has(est.id)}
                          onChange={() => toggleEstudio(est.id)}
                          className="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
                        />
                        <span className="text-sm text-va-heading">{est.nombre}</span>
                        {est.codigo && <span className="text-xs text-va-muted">({est.codigo})</span>}
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Modal>
    </div>
  );
}
