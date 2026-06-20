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

type PedidosCardProps = {
  atencionId: string;
  empleadoNombre?: string | null;
  empleadoFechaNacimiento?: string | null;
  empleadoObraSocial?: string | null;
  empleadoNroCarnet?: string | null;
};

export function PedidosCard({ atencionId, empleadoNombre, empleadoFechaNacimiento, empleadoObraSocial, empleadoNroCarnet }: PedidosCardProps) {
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

  async function handlePrint(ped: Pedido) {
    // Fetch config + signos vitales in parallel
    let config: Record<string, string> = {};
    let pesoKg: number | null = null;
    let alturaCm: number | null = null;
    try {
      const [cfgRes, svRes] = await Promise.all([
        http.get<{ clave: string; valor: string }[]>("/api/configuracion").catch(() => ({ data: [] as { clave: string; valor: string }[] })),
        http.get<{ peso_kg: number | null; altura_cm: number | null }>(`/api/signos-vitales/by-atencion/${atencionId}`).catch(() => ({ data: null })),
      ]);
      for (const c of cfgRes.data) config[c.clave] = c.valor;
      if (svRes.data) {
        pesoKg = svRes.data.peso_kg;
        alturaCm = svRes.data.altura_cm;
      }
    } catch { /* use defaults */ }

    const headerL1 = config.pdf_header_linea1 || "Municipalidad de Villa Allende";
    const headerL2 = config.pdf_header_linea2 || "Servicio de Medicina Laboral";
    const headerL3 = config.pdf_header_linea3 || "";
    const footer = config.pdf_footer || "";

    // Compute age
    let edad = "";
    if (empleadoFechaNacimiento) {
      const birth = new Date(empleadoFechaNacimiento);
      const today = new Date();
      let years = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) years--;
      edad = `${years} años`;
    }

    const fecha = new Date(ped.created_at).toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
    const tipoLabel = ped.tipo.charAt(0).toUpperCase() + ped.tipo.slice(1);

    // Build patient info parts
    const patientParts: string[] = [];
    if (empleadoNombre) patientParts.push(`<strong>Paciente:</strong> ${empleadoNombre}`);
    if (edad) patientParts.push(`<strong>Edad:</strong> ${edad}`);
    if (empleadoObraSocial) patientParts.push(`<strong>Obra social:</strong> ${empleadoObraSocial}`);
    if (empleadoNroCarnet) patientParts.push(`<strong>Nro. carnet:</strong> ${empleadoNroCarnet}`);
    if (pesoKg != null) patientParts.push(`<strong>Peso:</strong> ${pesoKg} kg`);
    if (alturaCm != null) patientParts.push(`<strong>Estatura:</strong> ${alturaCm} cm`);

    const win = window.open("", "_blank", "width=800,height=600");
    if (!win) return;

    // Build compact items list (two columns if many items)
    const itemsHtml = ped.items.map((it, i) =>
      `<tr><td style="width:20px;text-align:center;color:#718096;">${i + 1}</td><td>${it.descripcion}</td></tr>`
    ).join("");

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Pedido Medico - ${tipoLabel}</title>
<style>
  @page { size: A4; margin: 1.2cm 1.5cm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Arial, 'Segoe UI', sans-serif; font-size: 11px; color: #1a202c; }
  .header { text-align: center; border-bottom: 1.5px solid #2c5282; padding-bottom: 6px; margin-bottom: 8px; }
  .header h1 { font-size: 13px; color: #2c5282; margin: 0; line-height: 1.3; }
  .header h2 { font-size: 11px; color: #4a5568; font-weight: normal; margin: 0; line-height: 1.3; }
  .header p { font-size: 9px; color: #718096; margin: 0; }
  .title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .title-row h3 { font-size: 12px; font-weight: bold; color: #2d3748; }
  .badge { display: inline-block; padding: 1px 8px; border-radius: 3px; font-size: 9px; font-weight: 600; color: white; background: ${ped.tipo === "laboratorio" ? "#3182ce" : ped.tipo === "imagen" ? "#38a169" : ped.tipo === "interconsulta" ? "#d69e2e" : "#718096"}; }
  .patient { margin-bottom: 6px; padding: 4px 8px; background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 10px; line-height: 1.6; }
  .patient strong { color: #2d3748; }
  .meta { font-size: 10px; color: #4a5568; margin-bottom: 6px; }
  .meta strong { color: #2d3748; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
  th { text-align: left; padding: 3px 6px; background: #edf2f7; border: 1px solid #e2e8f0; font-size: 10px; color: #4a5568; }
  td { padding: 3px 6px; border: 1px solid #e2e8f0; font-size: 10px; }
  .firma-row { margin-top: 30px; display: flex; justify-content: flex-end; }
  .firma { text-align: center; border-top: 1px solid #1a202c; padding-top: 3px; min-width: 180px; font-size: 9px; color: #4a5568; }
  .page-footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #a0aec0; border-top: 1px solid #e2e8f0; padding: 4px 0; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
  <div class="header">
    <h1>${headerL1}</h1>
    <h2>${headerL2}</h2>
    ${headerL3 ? `<p>${headerL3}</p>` : ""}
  </div>
  <div class="title-row">
    <h3>Pedido Medico — <span class="badge">${tipoLabel}</span></h3>
    <span style="font-size:10px;color:#4a5568;">Fecha: ${fecha}</span>
  </div>
  <div class="patient">${patientParts.join(" &nbsp;|&nbsp; ")}</div>
  ${ped.diagnostico || ped.indicaciones ? `<div class="meta">${ped.diagnostico ? `<strong>Dx:</strong> ${ped.diagnostico}` : ""}${ped.diagnostico && ped.indicaciones ? " &nbsp;&mdash;&nbsp; " : ""}${ped.indicaciones ? `<strong>Indicaciones:</strong> ${ped.indicaciones}` : ""}</div>` : ""}
  <table>
    <thead><tr><th style="width:20px">#</th><th>Estudio / Practica</th></tr></thead>
    <tbody>${itemsHtml}</tbody>
  </table>
  <div class="firma-row"><div class="firma">Firma y sello del medico</div></div>
  ${footer ? `<div class="page-footer">${footer}</div>` : ""}
  <script>window.onload = function() { window.print(); }<\/script>
</body>
</html>`;
    win.document.write(html);
    win.document.close();
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
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handlePrint(ped)}
                  className="inline-flex items-center gap-1.5 text-sm text-accent-600 hover:text-accent-700 hover:underline"
                  title="Imprimir pedido"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5zm-3 0h.008v.008H15V10.5z" />
                  </svg>
                  Imprimir
                </button>
                <span className="text-xs text-va-muted">{new Date(ped.created_at).toLocaleString("es-AR")}</span>
              </div>
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
