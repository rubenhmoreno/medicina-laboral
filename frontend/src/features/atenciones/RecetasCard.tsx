import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Button, Card, CardBody, Input } from "@/components/ui";

type ItemReceta = {
  id: string;
  medicamento: string;
  dosis: string | null;
  frecuencia: string | null;
  duracion: string | null;
  orden: number;
};

type Receta = {
  id: string;
  atencion_id: string;
  medico_id: string;
  diagnostico: string | null;
  observaciones: string | null;
  created_at: string;
  items: ItemReceta[];
};

type ItemForm = { medicamento: string; dosis: string; frecuencia: string; duracion: string };

const EMPTY_ITEM: ItemForm = { medicamento: "", dosis: "", frecuencia: "", duracion: "" };

// Standard medications preloaded for quick selection
const MEDICAMENTOS_ESTANDAR = [
  // Analgesicos / Antiinflamatorios
  "Ibuprofeno 400mg",
  "Ibuprofeno 600mg",
  "Diclofenac 50mg",
  "Diclofenac 75mg",
  "Paracetamol 500mg",
  "Paracetamol 1g",
  "Meloxicam 15mg",
  "Ketorolac 10mg",
  "Naproxeno 550mg",
  "Dexametasona 4mg",
  "Dexametasona 8mg",
  "Betametasona 4mg",
  "Prednisona 5mg",
  "Prednisona 20mg",
  "Meprednisona 4mg",
  // Relajantes musculares
  "Ciclobenzaprina 10mg",
  "Orfenadrina 100mg",
  "Pridinol 4mg",
  // Antibioticos
  "Amoxicilina 500mg",
  "Amoxicilina 875mg / Clavulanico 125mg",
  "Azitromicina 500mg",
  "Cefalexina 500mg",
  "Ciprofloxacina 500mg",
  "Trimetoprima/Sulfametoxazol 160/800mg",
  // Gastrico
  "Omeprazol 20mg",
  "Ranitidina 150mg",
  "Metoclopramida 10mg",
  // Antialergicos
  "Loratadina 10mg",
  "Cetirizina 10mg",
  // Cardiovascular
  "Enalapril 10mg",
  "Losartan 50mg",
  "Atenolol 50mg",
  "Amlodipina 5mg",
  // Otros
  "Complejo B inyectable",
  "Dexametasona inyectable 4mg/ml",
  "Diclofenac inyectable 75mg/3ml",
  "Tramadol 50mg",
  "Pregabalina 75mg",
  "Pregabalina 150mg",
];

type RecetasCardProps = {
  atencionId: string;
  empleadoNombre?: string | null;
  empleadoLegajo?: string | null;
};

export function RecetasCard({ atencionId, empleadoNombre, empleadoLegajo }: RecetasCardProps) {
  const { user } = useAuth();
  const canEdit = user && (user.rol === "admin" || user.rol === "medico");
  const [rows, setRows] = useState<Receta[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [diagnostico, setDiagnostico] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [items, setItems] = useState<ItemForm[]>([{ ...EMPTY_ITEM }]);

  // Autocomplete state
  const [activeAutocomplete, setActiveAutocomplete] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Receta[]>(`/api/recetas/by-atencion/${atencionId}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [atencionId]);

  function addItem() {
    setItems((prev) => [...prev, { ...EMPTY_ITEM }]);
  }

  function removeItem(idx: number) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateItem(idx: number, key: keyof ItemForm, val: string) {
    setItems((prev) => prev.map((it, i) => i === idx ? { ...it, [key]: val } : it));
    if (key === "medicamento") {
      if (val.length >= 2) {
        const lower = val.toLowerCase();
        const matches = MEDICAMENTOS_ESTANDAR.filter((m) => m.toLowerCase().includes(lower));
        setSuggestions(matches);
        setActiveAutocomplete(idx);
      } else {
        setSuggestions([]);
        setActiveAutocomplete(null);
      }
    }
  }

  function selectSuggestion(idx: number, med: string) {
    setItems((prev) => prev.map((it, i) => i === idx ? { ...it, medicamento: med } : it));
    setSuggestions([]);
    setActiveAutocomplete(null);
  }

  function resetForm() {
    setDiagnostico("");
    setObservaciones("");
    setItems([{ ...EMPTY_ITEM }]);
    setShowForm(false);
    setSuggestions([]);
    setActiveAutocomplete(null);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const validItems = items.filter((it) => it.medicamento.trim());
    if (validItems.length === 0) return;
    setSaving(true);
    try {
      await http.post("/api/recetas", {
        atencion_id: atencionId,
        diagnostico: diagnostico || null,
        observaciones: observaciones || null,
        items: validItems.map((it) => ({
          medicamento: it.medicamento,
          dosis: it.dosis || null,
          frecuencia: it.frecuencia || null,
          duracion: it.duracion || null,
        })),
      });
      resetForm();
      await reload();
    } finally {
      setSaving(false);
    }
  }

  async function handlePrint(rec: Receta) {
    let config: Record<string, string> = {};
    try {
      const { data } = await http.get<{ clave: string; valor: string }[]>("/api/configuracion");
      for (const c of data) config[c.clave] = c.valor;
    } catch { /* use defaults */ }

    const headerL1 = config.pdf_header_linea1 || "Municipalidad de Villa Allende";
    const headerL2 = config.pdf_header_linea2 || "Servicio de Medicina Laboral";
    const headerL3 = config.pdf_header_linea3 || "";
    const footer = config.pdf_footer || "";

    const win = window.open("", "_blank", "width=800,height=600");
    if (!win) return;
    const fecha = new Date(rec.created_at).toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
    const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Receta Medica</title>
<style>
  @page { size: A5 landscape; margin: 1.5cm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #1a202c; padding: 20px; }
  .header { text-align: center; border-bottom: 2px solid #2c5282; padding-bottom: 12px; margin-bottom: 16px; }
  .header h1 { font-size: 16px; color: #2c5282; margin-bottom: 2px; }
  .header h2 { font-size: 13px; color: #4a5568; font-weight: normal; margin-bottom: 2px; }
  .header p { font-size: 10px; color: #718096; }
  .subtitle { text-align: center; font-size: 14px; font-weight: bold; color: #2d3748; margin-bottom: 16px; }
  .patient { margin-bottom: 12px; padding: 8px 12px; background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; }
  .patient strong { color: #2d3748; }
  .info { display: flex; justify-content: space-between; margin-bottom: 16px; font-size: 11px; }
  .rx { font-size: 28px; color: #2c5282; font-weight: bold; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
  th { text-align: left; padding: 6px 8px; background: #edf2f7; border: 1px solid #e2e8f0; font-size: 11px; color: #4a5568; }
  td { padding: 6px 8px; border: 1px solid #e2e8f0; font-size: 11px; }
  .dx { margin-bottom: 12px; font-size: 11px; }
  .dx strong { color: #2d3748; }
  .obs { margin-top: 8px; font-style: italic; color: #718096; font-size: 10px; }
  .footer-section { margin-top: 40px; display: flex; justify-content: space-between; align-items: flex-end; }
  .firma { text-align: center; border-top: 1px solid #1a202c; padding-top: 4px; min-width: 200px; font-size: 10px; }
  .page-footer { margin-top: 20px; text-align: center; font-size: 9px; color: #a0aec0; border-top: 1px solid #e2e8f0; padding-top: 8px; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
  <div class="header">
    <h1>${headerL1}</h1>
    <h2>${headerL2}</h2>
    ${headerL3 ? `<p>${headerL3}</p>` : ""}
  </div>
  <div class="subtitle">Receta Medica</div>
  <div class="patient">
    ${empleadoNombre ? `<strong>Paciente:</strong> ${empleadoNombre}` : ""}
    ${empleadoLegajo ? ` &nbsp;|&nbsp; <strong>Legajo:</strong> ${empleadoLegajo}` : ""}
  </div>
  <div class="info">
    <span>Fecha: ${fecha}</span>
  </div>
  ${rec.diagnostico ? `<div class="dx"><strong>Diagnostico:</strong> ${rec.diagnostico}</div>` : ""}
  <div class="rx">Rp/</div>
  <table>
    <thead>
      <tr><th>#</th><th>Medicamento</th><th>Dosis</th><th>Frecuencia</th><th>Duracion</th></tr>
    </thead>
    <tbody>
      ${rec.items.map((it, i) => `
        <tr>
          <td>${i + 1}</td>
          <td><strong>${it.medicamento}</strong></td>
          <td>${it.dosis ?? "—"}</td>
          <td>${it.frecuencia ?? "—"}</td>
          <td>${it.duracion ?? "—"}</td>
        </tr>
      `).join("")}
    </tbody>
  </table>
  ${rec.observaciones ? `<div class="obs">Obs: ${rec.observaciones}</div>` : ""}
  <div class="footer-section">
    <div></div>
    <div class="firma">Firma y sello del medico</div>
  </div>
  ${footer ? `<div class="page-footer">${footer}</div>` : ""}
  <script>window.onload = function() { window.print(); }<\/script>
</body>
</html>`;
    win.document.write(html);
    win.document.close();
  }

  if (loading) return <div className="text-sm text-va-muted py-4">Cargando recetas...</div>;

  return (
    <div className="space-y-4">
      {canEdit && !showForm && (
        <div className="flex justify-end">
          <Button onClick={() => setShowForm(true)}>Nueva receta</Button>
        </div>
      )}

      {showForm && (
        <Card>
          <CardBody>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading mb-4">Nueva receta</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Diagnostico</label>
                  <input
                    className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                    value={diagnostico} onChange={(e) => setDiagnostico(e.target.value)} placeholder="Diagnostico..."
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Observaciones</label>
                  <input
                    className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                    value={observaciones} onChange={(e) => setObservaciones(e.target.value)} placeholder="Observaciones..."
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-va-heading">Medicamentos</label>
                  <Button type="button" size="sm" variant="ghost" onClick={addItem}>+ Agregar</Button>
                </div>
                {items.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end">
                    <div className="col-span-4 relative">
                      <Input label={idx === 0 ? "Medicamento *" : undefined} value={item.medicamento}
                        onChange={(e) => updateItem(idx, "medicamento", e.target.value)}
                        onFocus={() => {
                          if (item.medicamento.length >= 2) {
                            const lower = item.medicamento.toLowerCase();
                            setSuggestions(MEDICAMENTOS_ESTANDAR.filter((m) => m.toLowerCase().includes(lower)));
                            setActiveAutocomplete(idx);
                          }
                        }}
                        onBlur={() => { setTimeout(() => { setActiveAutocomplete(null); setSuggestions([]); }, 200); }}
                        placeholder="Medicamento" required />
                      {activeAutocomplete === idx && suggestions.length > 0 && (
                        <div className="absolute z-20 left-0 right-0 top-full mt-1 max-h-48 overflow-y-auto rounded-lg border border-va-border bg-white shadow-lg">
                          {suggestions.map((med) => (
                            <button
                              key={med}
                              type="button"
                              className="block w-full px-3 py-2 text-left text-sm text-va-heading hover:bg-accent-50 transition-colors"
                              onMouseDown={(e) => { e.preventDefault(); selectSuggestion(idx, med); }}
                            >
                              {med}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="col-span-2">
                      <Input label={idx === 0 ? "Dosis" : undefined} value={item.dosis}
                        onChange={(e) => updateItem(idx, "dosis", e.target.value)} placeholder="Dosis" />
                    </div>
                    <div className="col-span-3">
                      <Input label={idx === 0 ? "Frecuencia" : undefined} value={item.frecuencia}
                        onChange={(e) => updateItem(idx, "frecuencia", e.target.value)} placeholder="Frecuencia" />
                    </div>
                    <div className="col-span-2">
                      <Input label={idx === 0 ? "Duracion" : undefined} value={item.duracion}
                        onChange={(e) => updateItem(idx, "duracion", e.target.value)} placeholder="Duracion" />
                    </div>
                    <div className="col-span-1">
                      {items.length > 1 && (
                        <button type="button" onClick={() => removeItem(idx)} className="p-2 text-red-500 hover:text-red-700">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" loading={saving}>Guardar receta</Button>
                <Button type="button" variant="ghost" onClick={resetForm}>Cancelar</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {rows.length === 0 && !showForm && (
        <Card>
          <CardBody className="text-center py-8">
            <p className="text-sm text-va-muted">No hay recetas registradas</p>
          </CardBody>
        </Card>
      )}

      {rows.map((rec) => (
        <Card key={rec.id}>
          <CardBody className="space-y-3">
            <div className="flex items-start justify-between">
              <h4 className="text-sm font-semibold text-va-heading">Receta</h4>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handlePrint(rec)}
                  className="inline-flex items-center gap-1.5 text-sm text-accent-600 hover:text-accent-700 hover:underline"
                  title="Imprimir receta"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5zm-3 0h.008v.008H15V10.5z" />
                  </svg>
                  Imprimir
                </button>
                <span className="text-xs text-va-muted">{new Date(rec.created_at).toLocaleString("es-AR")}</span>
              </div>
            </div>
            {rec.diagnostico && (
              <p className="text-sm"><span className="font-medium text-va-heading">Diagnostico: </span><span className="text-va-body">{rec.diagnostico}</span></p>
            )}
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-va-border">
                    <th className="text-left py-2 pr-4 font-medium text-va-muted">Medicamento</th>
                    <th className="text-left py-2 pr-4 font-medium text-va-muted">Dosis</th>
                    <th className="text-left py-2 pr-4 font-medium text-va-muted">Frecuencia</th>
                    <th className="text-left py-2 font-medium text-va-muted">Duracion</th>
                  </tr>
                </thead>
                <tbody>
                  {rec.items.map((it) => (
                    <tr key={it.id} className="border-b border-va-border/50">
                      <td className="py-2 pr-4 font-medium text-va-heading">{it.medicamento}</td>
                      <td className="py-2 pr-4 text-va-body">{it.dosis ?? "—"}</td>
                      <td className="py-2 pr-4 text-va-body">{it.frecuencia ?? "—"}</td>
                      <td className="py-2 text-va-body">{it.duracion ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rec.observaciones && (
              <p className="text-sm text-va-muted italic">{rec.observaciones}</p>
            )}
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
