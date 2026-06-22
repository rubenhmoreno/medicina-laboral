import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { licenciasApi, type Licencia } from "@/api/licencias";
import { adjuntosApi, validateFiles, type Adjunto } from "@/api/adjuntos";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Badge, Button, Card, CardBody, Modal, Input, PageHeader, Spinner } from "@/components/ui";

type ModalType = "validar" | "rechazar" | "anular" | null;

export function LicenciaDetailPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const [lic, setLic] = useState<Licencia | null>(null);
  const [tope, setTope] = useState<any | null>(null);
  const [adjuntos, setAdjuntos] = useState<Adjunto[]>([]);
  const [modal, setModal] = useState<ModalType>(null);
  const [diasOtorgados, setDiasOtorgados] = useState("");
  const [motivo, setMotivo] = useState("");
  const [modoConstatacion, setModoConstatacion] = useState("telefonica");
  const [actionLoading, setActionLoading] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  async function reload() {
    setLic(await licenciasApi.get(id));
    try { setTope(await licenciasApi.evaluarTope(id)); } catch { setTope(null); }
    try {
      const { data } = await http.get<Adjunto[]>(`/api/adjuntos/by-licencia/${id}`);
      setAdjuntos(data);
    } catch { setAdjuntos([]); }
  }
  useEffect(() => { reload(); }, [id]);

  async function handleAction() {
    setActionLoading(true);
    try {
      if (modal === "validar") {
        const d = parseInt(diasOtorgados, 10);
        if (Number.isFinite(d)) {
          await licenciasApi.validar(lic!.id, d, modoConstatacion);
        }
      } else if (modal === "rechazar") {
        if (motivo) await licenciasApi.rechazar(lic!.id, motivo);
      } else if (modal === "anular") {
        if (motivo) await licenciasApi.anular(lic!.id, motivo);
      }
      setModal(null);
      setMotivo("");
      setDiasOtorgados("");
      setModoConstatacion("telefonica");
      await reload();
    } finally {
      setActionLoading(false);
    }
  }

  async function handleUploadLic() {
    if (!uploadFiles.length) return;
    const sizeErr = validateFiles(uploadFiles);
    if (sizeErr) { alert(sizeErr); return; }
    setUploading(true);
    try {
      await adjuntosApi.uploadMany(uploadFiles, { licencia_id: id });
      setUploadFiles([]);
      await reload();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message ?? "Error al subir archivo");
    } finally {
      setUploading(false);
    }
  }

  async function handleDownload(adjId: string) {
    try {
      const { url } = await adjuntosApi.downloadUrl(adjId);
      window.open(url, "_blank");
    } catch {
      alert("Error al descargar");
    }
  }

  if (!lic) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" className="text-accent-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Detalle de licencia"
        subtitle={lic.empleado_nombre ?? `${lic.fecha_desde} - ${lic.fecha_hasta}`}
        actions={<Badge size="md">{lic.estado}</Badge>}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Datos del paciente */}
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Datos del paciente</h3>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="col-span-2">
                <p className="text-va-muted">Apellido y nombre</p>
                <p className="mt-1 font-semibold text-va-heading text-base">{lic.empleado_nombre ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">Legajo</p>
                <p className="mt-1 font-medium text-va-heading">{lic.empleado_legajo ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">CUIL</p>
                <p className="mt-1 font-medium text-va-heading font-mono">{lic.empleado_cuil ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">Fecha de nacimiento</p>
                <p className="mt-1 font-medium text-va-heading">{lic.empleado_fecha_nacimiento ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">Fecha de ingreso</p>
                <p className="mt-1 font-medium text-va-heading">{lic.empleado_fecha_ingreso ?? "—"}</p>
              </div>
              {lic.empleado_area_nombre && (
                <div className="col-span-2">
                  <p className="text-va-muted">Area</p>
                  <p className="mt-1 font-medium text-va-heading">{lic.empleado_area_nombre}</p>
                </div>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Informacion de la licencia */}
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Informacion de la licencia</h3>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {lic.tipo_licencia_nombre && (
                <div className="col-span-2">
                  <p className="text-va-muted">Tipo de licencia</p>
                  <p className="mt-1 font-medium text-va-heading">{lic.tipo_licencia_nombre}</p>
                </div>
              )}
              {lic.diagnostico && (
                <div className="col-span-2">
                  <p className="text-va-muted">Diagnostico</p>
                  <p className="mt-1 font-medium text-va-heading">{lic.diagnostico}</p>
                </div>
              )}
              <div>
                <p className="text-va-muted">Estado</p>
                <div className="mt-1"><Badge size="md">{lic.estado}</Badge></div>
              </div>
              <div>
                <p className="text-va-muted">Origen</p>
                <p className="mt-1 font-medium text-va-heading capitalize">{lic.origen}</p>
              </div>
              <div>
                <p className="text-va-muted">Fecha desde</p>
                <p className="mt-1 font-medium text-va-heading">{lic.fecha_desde}</p>
              </div>
              <div>
                <p className="text-va-muted">Fecha hasta</p>
                <p className="mt-1 font-medium text-va-heading">{lic.fecha_hasta}</p>
              </div>
              <div>
                <p className="text-va-muted">Dias solicitados</p>
                <p className="mt-1 font-medium text-va-heading">{lic.dias_solicitados}</p>
              </div>
              <div>
                <p className="text-va-muted">Dias otorgados</p>
                <p className="mt-1 font-medium text-va-heading">{lic.dias_otorgados ?? "—"}</p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Certificante y observaciones */}
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Certificante y observaciones</h3>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-va-muted">Certificante</p>
                <p className="mt-1 font-medium text-va-heading">{lic.certificante ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">Matricula</p>
                <p className="mt-1 font-medium text-va-heading">{lic.matricula_certificante ?? "—"}</p>
              </div>
              {lic.observaciones && (
                <div className="col-span-2">
                  <p className="text-va-muted">Observaciones</p>
                  <p className="mt-1 text-va-body">{lic.observaciones}</p>
                </div>
              )}
            </div>
            {lic.motivo_rechazo && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm">
                <p className="font-medium text-red-700">Motivo de rechazo</p>
                <p className="mt-1 text-red-600">{lic.motivo_rechazo}</p>
              </div>
            )}
            {lic.motivo_anulacion && (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm">
                <p className="font-medium text-amber-700">Motivo de anulacion</p>
                <p className="mt-1 text-amber-600">{lic.motivo_anulacion}</p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Gestion: quien cargo, quien valido */}
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Gestion</h3>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-va-muted">Cargada por</p>
                <p className="mt-1 font-medium text-va-heading">{lic.creado_por_nombre ?? "—"}</p>
              </div>
              <div>
                <p className="text-va-muted">Validada por</p>
                <p className="mt-1 font-medium text-va-heading">{lic.validado_por_nombre ?? "—"}</p>
              </div>
              {lic.validado_en && (
                <div>
                  <p className="text-va-muted">Fecha de validacion</p>
                  <p className="mt-1 font-medium text-va-heading">
                    {new Date(lic.validado_en).toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" })}
                  </p>
                </div>
              )}
              {lic.modo_constatacion && (
                <div>
                  <p className="text-va-muted">Modo de constatacion</p>
                  <p className="mt-1 font-medium text-va-heading capitalize">
                    {lic.modo_constatacion === "no_necesaria" ? "No necesario verificar" : lic.modo_constatacion === "telefonica" ? "Telefonica" : lic.modo_constatacion === "domicilio" ? "Domicilio" : lic.modo_constatacion === "consultorio" ? "Consultorio" : lic.modo_constatacion}
                  </p>
                </div>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Tope info */}
        {tope && tope.tope_aplicable !== null && (
          <Card>
            <CardBody className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Informacion de tope</h3>
              </div>
              <div className="flex items-center gap-4">
                <div className={`rounded-full p-3 ${tope.excede ? "bg-red-100" : "bg-emerald-100"}`}>
                  {tope.excede ? (
                    <svg className="h-7 w-7 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                  ) : (
                    <svg className="h-7 w-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-va-heading">
                    {tope.dias_consumidos_ventana} / {tope.tope_aplicable} dias
                  </p>
                  <p className={`text-sm ${tope.excede ? "text-red-600 font-medium" : "text-va-muted"}`}>
                    {tope.warning_msg || "Dentro del limite"}
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        )}
      </div>

      {/* Adjuntos */}
      <Card>
        <CardBody className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Adjuntos</h3>
          </div>

          {adjuntos.length === 0 && (
            <p className="text-sm text-va-muted">Sin adjuntos</p>
          )}

          <div className="space-y-3">
            {adjuntos.map((adj) => (
              <div key={adj.id} className="flex items-center gap-4 rounded-lg border border-va-border p-3">
                {adj.mime_type.startsWith("image/") && (
                  <AdjuntoThumbnail adjId={adj.id} alt={adj.nombre_original} />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-va-heading truncate">{adj.nombre_original}</p>
                  <p className="text-xs text-va-muted">{adj.mime_type} - {Math.round(adj.size_bytes / 1024)} KB</p>
                </div>
                <button onClick={() => handleDownload(adj.id)} className="shrink-0 text-sm text-accent-600 hover:underline">
                  {adj.mime_type === "application/pdf" ? "Ver PDF" : "Descargar"}
                </button>
              </div>
            ))}
          </div>

          {user && (user.rol === "admin" || user.rol === "rrhh" || user.rol === "medico") && (
            <div className="border-t border-va-border pt-4">
              <label className="mb-1.5 block text-sm font-medium text-va-heading">Subir archivos (max 5 MB c/u)</label>
              <div className="flex gap-2">
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.webp"
                  multiple
                  onChange={(e) => setUploadFiles(e.target.files ? Array.from(e.target.files) : [])}
                  className="block flex-1 text-sm text-va-body file:mr-3 file:rounded-lg file:border-0 file:bg-accent-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-accent-700 hover:file:bg-accent-100"
                />
                <Button size="sm" onClick={handleUploadLic} disabled={!uploadFiles.length} loading={uploading}>
                  Subir
                </Button>
              </div>
              {uploadFiles.length > 0 && (
                <p className="mt-1 text-xs text-va-muted">{uploadFiles.length} archivo(s) seleccionado(s)</p>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        {lic.estado === "borrador" && (
          <Button onClick={async () => { await licenciasApi.enviar(lic.id); await reload(); }}>
            Enviar
          </Button>
        )}
        {lic.estado === "enviado" && user?.rol === "medico" && (
          <>
            <Button
              onClick={() => { setDiasOtorgados(String(lic.dias_solicitados)); setModal("validar"); }}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              Validar
            </Button>
            <Button variant="danger" onClick={() => setModal("rechazar")}>
              Rechazar
            </Button>
          </>
        )}
        {lic.estado === "validado" && user?.rol === "admin" && (
          <Button
            onClick={() => setModal("anular")}
            className="bg-amber-600 hover:bg-amber-700 text-white"
          >
            Anular
          </Button>
        )}
      </div>

      {/* Modal: Validar */}
      <Modal
        open={modal === "validar"}
        onClose={() => setModal(null)}
        title="Validar licencia"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModal(null)}>Cancelar</Button>
            <Button onClick={handleAction} loading={actionLoading} className="bg-emerald-600 hover:bg-emerald-700">
              Confirmar validacion
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {lic.empleado_telefono && (
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
              <p className="text-xs text-blue-600 font-medium uppercase tracking-wider">Telefono del paciente</p>
              <p className="mt-1 text-base font-semibold text-blue-800 font-mono">{lic.empleado_telefono}</p>
            </div>
          )}

          <Input
            label="Dias a otorgar"
            type="number"
            value={diasOtorgados}
            onChange={(e) => setDiasOtorgados(e.target.value)}
            min={1}
            required
          />

          <div>
            <p className="mb-2 text-sm font-medium text-va-heading">Modo de constatacion</p>
            <div className="space-y-2">
              {[
                { value: "telefonica", label: "Telefonica" },
                { value: "domicilio", label: "Domicilio" },
                { value: "consultorio", label: "Consultorio" },
                { value: "no_necesaria", label: "No era necesario verificar" },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="modo_constatacion"
                    value={opt.value}
                    checked={modoConstatacion === opt.value}
                    onChange={(e) => setModoConstatacion(e.target.value)}
                    className="h-4 w-4 text-accent-600 border-va-border focus:ring-accent-500"
                  />
                  <span className="text-sm text-va-body">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </Modal>

      {/* Modal: Rechazar */}
      <Modal
        open={modal === "rechazar"}
        onClose={() => setModal(null)}
        title="Rechazar licencia"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModal(null)}>Cancelar</Button>
            <Button variant="danger" onClick={handleAction} loading={actionLoading}>
              Confirmar rechazo
            </Button>
          </>
        }
      >
        <Input
          label="Motivo de rechazo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          required
          placeholder="Ingrese el motivo..."
        />
      </Modal>

      {/* Modal: Anular */}
      <Modal
        open={modal === "anular"}
        onClose={() => setModal(null)}
        title="Anular licencia"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModal(null)}>Cancelar</Button>
            <Button onClick={handleAction} loading={actionLoading} className="bg-amber-600 hover:bg-amber-700 text-white">
              Confirmar anulacion
            </Button>
          </>
        }
      >
        <Input
          label="Motivo de anulacion"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          required
          placeholder="Ingrese el motivo..."
        />
      </Modal>
    </div>
  );
}

function AdjuntoThumbnail({ adjId, alt }: { adjId: string; alt: string }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    adjuntosApi.downloadUrl(adjId).then(({ url }) => setSrc(url)).catch(() => {});
  }, [adjId]);
  if (!src) return null;
  return <img src={src} alt={alt} className="h-16 w-16 rounded-lg object-cover border border-va-border" />;
}
