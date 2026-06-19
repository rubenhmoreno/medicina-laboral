import { useEffect, useState, type FormEvent } from "react";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Button, Card, CardBody, Input } from "@/components/ui";

type SignosVitales = {
  id: string;
  atencion_id: string;
  peso_kg: number | null;
  altura_cm: number | null;
  imc: number | null;
  presion_sistolica: number | null;
  presion_diastolica: number | null;
  temperatura: number | null;
  frecuencia_cardiaca: number | null;
  saturacion_o2: number | null;
  glucemia: number | null;
  registrado_por: string;
  created_at: string;
  updated_at: string;
};

const EMPTY_FORM = {
  peso_kg: "", altura_cm: "", presion_sistolica: "", presion_diastolica: "",
  temperatura: "", frecuencia_cardiaca: "", saturacion_o2: "", glucemia: "",
};

export function SignosVitalesCard({ atencionId }: { atencionId: string }) {
  const { user } = useAuth();
  const canEdit = user && (user.rol === "admin" || user.rol === "medico");
  const [data, setData] = useState<SignosVitales | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  async function reload() {
    setLoading(true);
    try {
      const { data: sv } = await http.get<SignosVitales | null>(`/api/signos-vitales/by-atencion/${atencionId}`);
      setData(sv);
      if (sv) {
        setForm({
          peso_kg: sv.peso_kg?.toString() ?? "",
          altura_cm: sv.altura_cm?.toString() ?? "",
          presion_sistolica: sv.presion_sistolica?.toString() ?? "",
          presion_diastolica: sv.presion_diastolica?.toString() ?? "",
          temperatura: sv.temperatura?.toString() ?? "",
          frecuencia_cardiaca: sv.frecuencia_cardiaca?.toString() ?? "",
          saturacion_o2: sv.saturacion_o2?.toString() ?? "",
          glucemia: sv.glucemia?.toString() ?? "",
        });
      }
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [atencionId]);

  function num(v: string): number | null {
    const n = parseFloat(v);
    return isNaN(n) ? null : n;
  }

  function intNum(v: string): number | null {
    const n = parseInt(v, 10);
    return isNaN(n) ? null : n;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const body = {
        peso_kg: num(form.peso_kg),
        altura_cm: num(form.altura_cm),
        presion_sistolica: intNum(form.presion_sistolica),
        presion_diastolica: intNum(form.presion_diastolica),
        temperatura: num(form.temperatura),
        frecuencia_cardiaca: intNum(form.frecuencia_cardiaca),
        saturacion_o2: intNum(form.saturacion_o2),
        glucemia: num(form.glucemia),
      };
      if (data) {
        await http.put(`/api/signos-vitales/${data.id}`, body);
      } else {
        await http.post("/api/signos-vitales", { atencion_id: atencionId, ...body });
      }
      setEditing(false);
      await reload();
    } finally {
      setSaving(false);
    }
  }

  function setF(k: keyof typeof form, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  if (loading) return <div className="text-sm text-va-muted py-4">Cargando signos vitales...</div>;

  if (!data && !editing) {
    return (
      <Card>
        <CardBody className="text-center py-8">
          <p className="text-sm text-va-muted mb-4">No se registraron signos vitales</p>
          {canEdit && <Button onClick={() => setEditing(true)}>Registrar signos vitales</Button>}
        </CardBody>
      </Card>
    );
  }

  if (editing || !data) {
    return (
      <Card>
        <CardBody>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading mb-4">
            {data ? "Editar signos vitales" : "Registrar signos vitales"}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Input label="Peso (kg)" type="number" step="0.1" value={form.peso_kg} onChange={(e) => setF("peso_kg", e.target.value)} />
              <Input label="Altura (cm)" type="number" step="0.1" value={form.altura_cm} onChange={(e) => setF("altura_cm", e.target.value)} />
              <Input label="PA Sistolica" type="number" value={form.presion_sistolica} onChange={(e) => setF("presion_sistolica", e.target.value)} />
              <Input label="PA Diastolica" type="number" value={form.presion_diastolica} onChange={(e) => setF("presion_diastolica", e.target.value)} />
              <Input label="Temperatura" type="number" step="0.1" value={form.temperatura} onChange={(e) => setF("temperatura", e.target.value)} />
              <Input label="Frec. cardiaca" type="number" value={form.frecuencia_cardiaca} onChange={(e) => setF("frecuencia_cardiaca", e.target.value)} />
              <Input label="Sat O2 (%)" type="number" value={form.saturacion_o2} onChange={(e) => setF("saturacion_o2", e.target.value)} />
              <Input label="Glucemia" type="number" step="0.1" value={form.glucemia} onChange={(e) => setF("glucemia", e.target.value)} />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" loading={saving}>Guardar</Button>
              {data && <Button type="button" variant="ghost" onClick={() => setEditing(false)}>Cancelar</Button>}
            </div>
          </form>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Signos vitales</h3>
          {canEdit && (
            <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>Editar</Button>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          {data.peso_kg != null && (
            <div>
              <span className="text-va-muted">Peso</span>
              <p className="font-medium text-va-heading">{data.peso_kg} kg</p>
            </div>
          )}
          {data.altura_cm != null && (
            <div>
              <span className="text-va-muted">Altura</span>
              <p className="font-medium text-va-heading">{data.altura_cm} cm</p>
            </div>
          )}
          {data.imc != null && (
            <div>
              <span className="text-va-muted">IMC</span>
              <p className="font-medium text-va-heading">{data.imc}</p>
            </div>
          )}
          {(data.presion_sistolica != null || data.presion_diastolica != null) && (
            <div>
              <span className="text-va-muted">Presion arterial</span>
              <p className="font-medium text-va-heading">
                {data.presion_sistolica ?? "—"}/{data.presion_diastolica ?? "—"} mmHg
              </p>
            </div>
          )}
          {data.temperatura != null && (
            <div>
              <span className="text-va-muted">Temperatura</span>
              <p className="font-medium text-va-heading">{data.temperatura} °C</p>
            </div>
          )}
          {data.frecuencia_cardiaca != null && (
            <div>
              <span className="text-va-muted">Frec. cardiaca</span>
              <p className="font-medium text-va-heading">{data.frecuencia_cardiaca} bpm</p>
            </div>
          )}
          {data.saturacion_o2 != null && (
            <div>
              <span className="text-va-muted">Sat O2</span>
              <p className="font-medium text-va-heading">{data.saturacion_o2}%</p>
            </div>
          )}
          {data.glucemia != null && (
            <div>
              <span className="text-va-muted">Glucemia</span>
              <p className="font-medium text-va-heading">{data.glucemia} mg/dL</p>
            </div>
          )}
        </div>
        <p className="mt-3 text-xs text-va-muted">
          Registrado el {new Date(data.created_at).toLocaleString("es-AR")}
        </p>
      </CardBody>
    </Card>
  );
}
