import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Badge, Button, Card, CardBody, Modal, PageHeader } from "@/components/ui";
import { Tabs } from "@/components/ui/Tabs";
import { SignosVitalesCard } from "./SignosVitalesCard";
import { EvolucionesCard } from "./EvolucionesCard";
import { RecetasCard } from "./RecetasCard";
import { PedidosCard } from "./PedidosCard";

type Atencion = {
  id: string; empleado_id: string; asignado_por: string;
  medico_id: string | null; fecha_turno: string; motivo: string;
  estado: string; notas_medicas: string | null;
  created_at: string; updated_at: string;
  empleado_nombre?: string | null;
  empleado_legajo?: string | null;
  empleado_cuil?: string | null;
  medico_nombre?: string | null;
};

type Adjunto = {
  id: string; nombre_original: string; mime_type: string;
  size_bytes: number; created_at: string;
};

const ESTADO_COLORS: Record<string, "amber" | "green" | "red"> = {
  pendiente: "amber",
  completada: "green",
  cancelada: "red",
};

const TABS = [
  { key: "info", label: "Informacion" },
  { key: "signos", label: "Signos Vitales" },
  { key: "evolucion", label: "Evolucion" },
  { key: "recetas", label: "Recetas" },
  { key: "pedidos", label: "Pedidos" },
  { key: "adjuntos", label: "Adjuntos" },
];

export function AtencionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const { user } = useAuth();
  const [atencion, setAtencion] = useState<Atencion | null>(null);
  const [adjuntos, setAdjuntos] = useState<Adjunto[]>([]);
  const [loading, setLoading] = useState(true);
  const [completarOpen, setCompletarOpen] = useState(false);
  const [notas, setNotas] = useState("");
  const [saving, setSaving] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState("info");

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<Atencion>(`/api/atenciones/${id}`);
      setAtencion(data);
      const adjRes = await http.get<Adjunto[]>(`/api/adjuntos/by-atencion/${id}`).catch(() => ({ data: [] as Adjunto[] }));
      setAdjuntos(adjRes.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [id]);

  async function handleCompletar() {
    setSaving(true);
    try {
      await http.post(`/api/atenciones/${id}/completar`, { notas_medicas: notas || null });
      setCompletarOpen(false);
      setNotas("");
      await reload();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.response?.data?.error?.message ?? "Error al completar la atencion";
      alert(msg);
      setCompletarOpen(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleCancelar() {
    if (!confirm("Cancelar esta atencion?")) return;
    setSaving(true);
    try {
      await http.post(`/api/atenciones/${id}/cancelar`);
      await reload();
    } finally {
      setSaving(false);
    }
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("atencion_id", id!);
      fd.append("file", file);
      await http.post("/api/adjuntos", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setFile(null);
      await reload();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message ?? "Error al subir archivo");
    } finally {
      setUploading(false);
    }
  }

  async function handleDownload(adjId: string) {
    try {
      const { data } = await http.get<{ url: string }>(`/api/adjuntos/${adjId}/download`);
      window.open(data.url, "_blank");
    } catch {
      alert("Error al descargar");
    }
  }

  if (loading) return <div className="p-6 text-va-muted">Cargando...</div>;
  if (!atencion) return <div className="p-6 text-red-600">Atencion no encontrada</div>;

  const isPendiente = atencion.estado === "pendiente";
  const canComplete = isPendiente && user && (user.rol === "admin" || user.rol === "medico");
  const canCancel = isPendiente && user && (user.rol === "admin" || user.rol === "rrhh");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Detalle de atencion"
        subtitle={atencion.empleado_nombre ?? `Creada el ${new Date(atencion.created_at).toLocaleString("es-AR")}`}
        actions={
          <Button variant="ghost" onClick={() => nav("/atenciones")}>Volver</Button>
        }
      />

      <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />

      <div className="mt-4">
        {activeTab === "info" && (
          <Card>
            <CardBody className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Informacion</h3>
                <Badge variant={ESTADO_COLORS[atencion.estado]}>{atencion.estado}</Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="col-span-2">
                  <span className="text-va-muted">Paciente</span>
                  <p className="mt-1 font-semibold text-va-heading text-base">{atencion.empleado_nombre ?? "—"}</p>
                </div>
                {atencion.empleado_legajo && (
                  <div>
                    <span className="text-va-muted">Legajo</span>
                    <p className="font-medium text-va-heading">{atencion.empleado_legajo}</p>
                  </div>
                )}
                {atencion.empleado_cuil && (
                  <div>
                    <span className="text-va-muted">CUIL</span>
                    <p className="font-medium text-va-heading font-mono">{atencion.empleado_cuil}</p>
                  </div>
                )}
                <div>
                  <span className="text-va-muted">Fecha turno</span>
                  <p className="font-medium text-va-heading">
                    {new Date(atencion.fecha_turno).toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" })}
                  </p>
                </div>
                {atencion.medico_nombre && (
                  <div>
                    <span className="text-va-muted">Medico</span>
                    <p className="font-medium text-va-heading">{atencion.medico_nombre}</p>
                  </div>
                )}
                <div className="col-span-2">
                  <span className="text-va-muted">Motivo</span>
                  <p className="text-va-heading">{atencion.motivo}</p>
                </div>
              </div>

              {atencion.notas_medicas && (
                <div>
                  <span className="text-sm text-va-muted">Notas medicas</span>
                  <p className="mt-1 rounded-lg bg-blue-50 border border-blue-200 p-3 text-sm text-blue-800">
                    {atencion.notas_medicas}
                  </p>
                </div>
              )}

              {isPendiente && (
                <div className="flex gap-3 pt-2">
                  {canComplete && (
                    <Button onClick={() => setCompletarOpen(true)}>Completar atencion</Button>
                  )}
                  {canCancel && (
                    <Button variant="secondary" onClick={handleCancelar} loading={saving}>Cancelar turno</Button>
                  )}
                </div>
              )}
            </CardBody>
          </Card>
        )}

        {activeTab === "signos" && (
          <SignosVitalesCard atencionId={id!} />
        )}

        {activeTab === "evolucion" && (
          <EvolucionesCard atencionId={id!} />
        )}

        {activeTab === "recetas" && (
          <RecetasCard atencionId={id!} />
        )}

        {activeTab === "pedidos" && (
          <PedidosCard atencionId={id!} />
        )}

        {activeTab === "adjuntos" && (
          <Card>
            <CardBody className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Adjuntos</h3>

              {adjuntos.length === 0 && (
                <p className="text-sm text-va-muted">Sin adjuntos</p>
              )}

              {adjuntos.map((adj) => (
                <div key={adj.id} className="flex items-center justify-between rounded-lg border border-va-border p-3">
                  <div>
                    <p className="text-sm font-medium text-va-heading">{adj.nombre_original}</p>
                    <p className="text-xs text-va-muted">{adj.mime_type} - {Math.round(adj.size_bytes / 1024)} KB</p>
                  </div>
                  <button onClick={() => handleDownload(adj.id)} className="text-sm text-accent-600 hover:underline">
                    Descargar
                  </button>
                </div>
              ))}

              {user && (user.rol === "admin" || user.rol === "medico") && (
                <div className="border-t border-va-border pt-4">
                  <label className="mb-1.5 block text-sm font-medium text-va-heading">Subir archivo</label>
                  <div className="flex gap-2">
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="block flex-1 text-sm text-va-body file:mr-3 file:rounded-lg file:border-0 file:bg-accent-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-accent-700 hover:file:bg-accent-100"
                    />
                    <Button size="sm" onClick={handleUpload} disabled={!file} loading={uploading}>
                      Subir
                    </Button>
                  </div>
                </div>
              )}
            </CardBody>
          </Card>
        )}
      </div>

      <Modal
        open={completarOpen}
        onClose={() => setCompletarOpen(false)}
        title="Completar atencion"
        size="md"
        actions={
          <>
            <Button variant="secondary" onClick={() => setCompletarOpen(false)}>Cancelar</Button>
            <Button onClick={handleCompletar} loading={saving}>Confirmar</Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-va-heading">Notas medicas (opcional)</label>
            <textarea
              className="block w-full rounded-lg border border-va-border bg-va-card px-3 py-2 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
              rows={4}
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              placeholder="Observaciones de la consulta..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
