import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Button, Card, CardBody } from "@/components/ui";

type Evolucion = {
  id: string;
  atencion_id: string;
  motivo_consulta: string;
  anamnesis: string | null;
  examen_fisico: string | null;
  diagnostico_presuntivo: string | null;
  diagnostico_definitivo: string | null;
  tratamiento: string | null;
  observaciones: string | null;
  medico_id: string;
  created_at: string;
  updated_at: string;
};

const EMPTY_FORM = {
  motivo_consulta: "", anamnesis: "", examen_fisico: "",
  diagnostico_presuntivo: "", diagnostico_definitivo: "",
  tratamiento: "", observaciones: "",
};

export function EvolucionesCard({ atencionId }: { atencionId: string }) {
  const { user } = useAuth();
  const canEdit = user && (user.rol === "admin" || user.rol === "medico");
  const [rows, setRows] = useState<Evolucion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Evolucion[]>(`/api/evoluciones/by-atencion/${atencionId}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, [atencionId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await http.post("/api/evoluciones", {
        atencion_id: atencionId,
        motivo_consulta: form.motivo_consulta,
        anamnesis: form.anamnesis || null,
        examen_fisico: form.examen_fisico || null,
        diagnostico_presuntivo: form.diagnostico_presuntivo || null,
        diagnostico_definitivo: form.diagnostico_definitivo || null,
        tratamiento: form.tratamiento || null,
        observaciones: form.observaciones || null,
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await reload();
    } finally {
      setSaving(false);
    }
  }

  function setF(k: keyof typeof form, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  if (loading) return <div className="text-sm text-va-muted py-4">Cargando evoluciones...</div>;

  return (
    <div className="space-y-4">
      {canEdit && !showForm && (
        <div className="flex justify-end">
          <Button onClick={() => setShowForm(true)}>Nueva evolucion</Button>
        </div>
      )}

      {showForm && (
        <Card>
          <CardBody>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading mb-4">Nueva evolucion clinica</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Motivo de consulta *</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={2} value={form.motivo_consulta} onChange={(e) => setF("motivo_consulta", e.target.value)} required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Anamnesis</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={3} value={form.anamnesis} onChange={(e) => setF("anamnesis", e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Examen fisico</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={3} value={form.examen_fisico} onChange={(e) => setF("examen_fisico", e.target.value)}
                />
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Diagnostico presuntivo</label>
                  <textarea
                    className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                    rows={2} value={form.diagnostico_presuntivo} onChange={(e) => setF("diagnostico_presuntivo", e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Diagnostico definitivo</label>
                  <textarea
                    className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                    rows={2} value={form.diagnostico_definitivo} onChange={(e) => setF("diagnostico_definitivo", e.target.value)}
                    placeholder="Escriba el diagnostico definitivo"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Tratamiento</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={2} value={form.tratamiento} onChange={(e) => setF("tratamiento", e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-va-heading">Observaciones</label>
                <textarea
                  className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
                  rows={2} value={form.observaciones} onChange={(e) => setF("observaciones", e.target.value)}
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button type="submit" loading={saving}>Guardar</Button>
                <Button type="button" variant="ghost" onClick={() => { setShowForm(false); setForm(EMPTY_FORM); }}>Cancelar</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {rows.length === 0 && !showForm && (
        <Card>
          <CardBody className="text-center py-8">
            <p className="text-sm text-va-muted">No hay evoluciones registradas</p>
          </CardBody>
        </Card>
      )}

      {rows.map((ev) => (
        <Card key={ev.id}>
          <CardBody className="space-y-3">
            <div className="flex items-start justify-between">
              <h4 className="text-sm font-semibold text-va-heading">Evolucion</h4>
              <span className="text-xs text-va-muted">{new Date(ev.created_at).toLocaleString("es-AR")}</span>
            </div>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-va-heading">Motivo: </span>
                <span className="text-va-body">{ev.motivo_consulta}</span>
              </div>
              {ev.anamnesis && (
                <div>
                  <span className="font-medium text-va-heading">Anamnesis: </span>
                  <span className="text-va-body">{ev.anamnesis}</span>
                </div>
              )}
              {ev.examen_fisico && (
                <div>
                  <span className="font-medium text-va-heading">Examen fisico: </span>
                  <span className="text-va-body">{ev.examen_fisico}</span>
                </div>
              )}
              {ev.diagnostico_presuntivo && (
                <div>
                  <span className="font-medium text-va-heading">Dx presuntivo: </span>
                  <span className="text-va-body">{ev.diagnostico_presuntivo}</span>
                </div>
              )}
              {ev.diagnostico_definitivo && (
                <div>
                  <span className="font-medium text-va-heading">Dx definitivo: </span>
                  <span className="text-va-body">{ev.diagnostico_definitivo}</span>
                </div>
              )}
              {ev.tratamiento && (
                <div>
                  <span className="font-medium text-va-heading">Tratamiento: </span>
                  <span className="text-va-body">{ev.tratamiento}</span>
                </div>
              )}
              {ev.observaciones && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
                  <span className="font-medium text-amber-800">Obs: </span>
                  <span className="text-amber-700">{ev.observaciones}</span>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
