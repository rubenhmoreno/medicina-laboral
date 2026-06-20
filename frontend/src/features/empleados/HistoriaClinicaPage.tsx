import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { http } from "@/api/http";
import { Badge, Button, Card, CardBody, PageHeader, Spinner } from "@/components/ui";

type Empleado = {
  id: string; legajo: string; cuil: string;
  nombre: string; apellido: string;
  fecha_nacimiento: string | null; fecha_ingreso: string;
  activo: boolean;
};

type SignosVitales = {
  peso_kg: number | null; altura_cm: number | null; imc: number | null;
  presion_sistolica: number | null; presion_diastolica: number | null;
  temperatura: number | null; frecuencia_cardiaca: number | null;
  saturacion_o2: number | null; glucemia: number | null;
};

type Evolucion = {
  id: string; motivo_consulta: string; anamnesis: string | null;
  examen_fisico: string | null; diagnostico_presuntivo: string | null;
  diagnostico_definitivo: string | null;
  tratamiento: string | null; observaciones: string | null;
};

type ItemReceta = { medicamento: string; dosis: string | null; frecuencia: string | null; duracion: string | null };
type Receta = { id: string; diagnostico: string | null; observaciones: string | null; items: ItemReceta[] };

type ItemPedido = { descripcion: string; codigo: string | null };
type Pedido = { id: string; tipo: string; diagnostico: string | null; indicaciones: string | null; items: ItemPedido[] };

type AtencionConDetalles = {
  atencion: {
    id: string; fecha_turno: string; motivo: string; estado: string;
    notas_medicas: string | null;
  };
  signos_vitales: SignosVitales | null;
  evoluciones: Evolucion[];
  recetas: Receta[];
  pedidos: Pedido[];
};

type Licencia = {
  id: string; fecha_desde: string; fecha_hasta: string;
  dias_solicitados: number; dias_otorgados: number | null;
  estado: string; empleado_nombre: string | null;
  tipo_licencia_nombre: string | null; diagnostico: string | null;
  certificante: string | null; observaciones: string | null;
  modo_constatacion: string | null;
};

type HistoriaClinica = {
  empleado: Empleado;
  licencias: Licencia[];
  atenciones: AtencionConDetalles[];
};

export function HistoriaClinicaPage() {
  const { id } = useParams<{ id: string }>();
  const [hc, setHc] = useState<HistoriaClinica | null>(null);
  const [loading, setLoading] = useState(true);
  const [licOpen, setLicOpen] = useState(true);
  const [atenOpen, setAtenOpen] = useState(true);

  useEffect(() => {
    http.get<HistoriaClinica>(`/api/empleados/${id}/historia-clinica`)
      .then(({ data }) => setHc(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  function handleExportPdf() {
    http.get(`/api/empleados/${id}/historia-clinica/pdf`, { responseType: "blob" })
      .then(({ data }) => {
        const url = URL.createObjectURL(data);
        const a = document.createElement("a");
        a.href = url;
        a.download = `historia_clinica_${hc?.empleado.legajo ?? id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Error al exportar PDF"));
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" className="text-accent-500" />
      </div>
    );
  }

  if (!hc) return <div className="p-6 text-red-600">No se pudo cargar la historia clinica</div>;

  const emp = hc.empleado;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Historia Clinica"
        subtitle={`${emp.apellido}, ${emp.nombre} — Legajo ${emp.legajo}`}
        actions={
          <Button onClick={handleExportPdf}>
            <svg className="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Exportar PDF
          </Button>
        }
      />

      {/* Datos del empleado */}
      <Card>
        <CardBody className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">Datos del empleado</h3>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <div>
              <p className="text-va-muted">Legajo</p>
              <p className="font-medium text-va-heading">{emp.legajo}</p>
            </div>
            <div>
              <p className="text-va-muted">CUIL</p>
              <p className="font-medium text-va-heading font-mono">{emp.cuil}</p>
            </div>
            <div>
              <p className="text-va-muted">Fecha nacimiento</p>
              <p className="font-medium text-va-heading">{emp.fecha_nacimiento ?? "—"}</p>
            </div>
            <div>
              <p className="text-va-muted">Fecha ingreso</p>
              <p className="font-medium text-va-heading">{emp.fecha_ingreso}</p>
            </div>
            <div>
              <p className="text-va-muted">Estado</p>
              <Badge>{emp.activo ? "activo" : "inactivo"}</Badge>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Licencias */}
      <Card>
        <CardBody>
          <button
            className="flex w-full items-center justify-between"
            onClick={() => setLicOpen(!licOpen)}
          >
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
                Licencias ({hc.licencias.length})
              </h3>
            </div>
            <svg className={`h-5 w-5 text-va-muted transition-transform ${licOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>
          {licOpen && (
            <div className="mt-4 space-y-2">
              {hc.licencias.length === 0 && <p className="text-sm text-va-muted">Sin licencias registradas</p>}
              {hc.licencias.map((lic) => (
                <Link key={lic.id} to={`/licencias/${lic.id}`} className="block rounded-lg border border-va-border p-3 text-sm hover:border-accent-400 hover:shadow-sm transition-all">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-va-heading">
                      {lic.fecha_desde} - {lic.fecha_hasta}
                      {lic.tipo_licencia_nombre && <span className="ml-2 text-va-muted">({lic.tipo_licencia_nombre})</span>}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{lic.dias_otorgados ?? lic.dias_solicitados} dias</span>
                      <Badge>{lic.estado}</Badge>
                    </div>
                  </div>
                  {lic.diagnostico && (
                    <p className="mt-1 text-va-muted">Dx: {lic.diagnostico}</p>
                  )}
                  {lic.certificante && (
                    <p className="mt-1 text-va-muted">Certificante: {lic.certificante}</p>
                  )}
                  {lic.modo_constatacion && (
                    <p className="mt-1 text-va-muted">Constatacion: {lic.modo_constatacion === "no_necesaria" ? "No necesaria" : lic.modo_constatacion === "telefonica" ? "Telefonica" : "Presencial"}</p>
                  )}
                  {lic.observaciones && (
                    <p className="mt-1 text-va-muted">Obs: {lic.observaciones}</p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Atenciones */}
      <Card>
        <CardBody>
          <button
            className="flex w-full items-center justify-between"
            onClick={() => setAtenOpen(!atenOpen)}
          >
            <div className="flex items-center gap-2">
              <div className="h-1 w-4 rounded-full gradient-va-horizontal" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
                Atenciones ({hc.atenciones.length})
              </h3>
            </div>
            <svg className={`h-5 w-5 text-va-muted transition-transform ${atenOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>
          {atenOpen && (
            <div className="mt-4 space-y-4">
              {hc.atenciones.length === 0 && <p className="text-sm text-va-muted">Sin atenciones registradas</p>}
              {hc.atenciones.map((ad) => (
                <Link key={ad.atencion.id} to={`/atenciones/${ad.atencion.id}`} className="block hover:shadow-sm transition-all">
                  <AtencionCard data={ad} />
                </Link>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function AtencionCard({ data }: { data: AtencionConDetalles }) {
  const a = data.atencion;
  const fecha = new Date(a.fecha_turno).toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" });

  return (
    <div className="rounded-lg border border-va-border p-4 space-y-3 hover:border-accent-400 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-va-heading">{fecha} — {a.motivo}</span>
        <Badge>{a.estado}</Badge>
      </div>

      {a.notas_medicas && (
        <p className="text-sm text-va-body rounded bg-blue-50 border border-blue-200 p-2">{a.notas_medicas}</p>
      )}

      {/* Signos vitales */}
      {data.signos_vitales && (
        <div className="text-sm">
          <p className="font-medium text-va-heading mb-1">Signos vitales</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-va-body">
            {data.signos_vitales.peso_kg != null && <span>Peso: {data.signos_vitales.peso_kg} kg</span>}
            {data.signos_vitales.altura_cm != null && <span>Altura: {data.signos_vitales.altura_cm} cm</span>}
            {data.signos_vitales.imc != null && <span>IMC: {data.signos_vitales.imc}</span>}
            {data.signos_vitales.presion_sistolica != null && data.signos_vitales.presion_diastolica != null && (
              <span>PA: {data.signos_vitales.presion_sistolica}/{data.signos_vitales.presion_diastolica}</span>
            )}
            {data.signos_vitales.temperatura != null && <span>Temp: {data.signos_vitales.temperatura}</span>}
            {data.signos_vitales.frecuencia_cardiaca != null && <span>FC: {data.signos_vitales.frecuencia_cardiaca}</span>}
            {data.signos_vitales.saturacion_o2 != null && <span>SpO2: {data.signos_vitales.saturacion_o2}%</span>}
            {data.signos_vitales.glucemia != null && <span>Glucemia: {data.signos_vitales.glucemia}</span>}
          </div>
        </div>
      )}

      {/* Evoluciones */}
      {data.evoluciones.map((ev) => (
        <div key={ev.id} className="text-sm border-t border-va-border pt-2">
          <p className="font-medium text-va-heading">Evolucion: {ev.motivo_consulta}</p>
          {ev.anamnesis && <p className="text-va-body">Anamnesis: {ev.anamnesis}</p>}
          {ev.examen_fisico && <p className="text-va-body">Examen fisico: {ev.examen_fisico}</p>}
          {ev.diagnostico_presuntivo && <p className="text-va-body">Dx presuntivo: {ev.diagnostico_presuntivo}</p>}
          {ev.diagnostico_definitivo && <p className="text-va-body">Dx definitivo: {ev.diagnostico_definitivo}</p>}
          {ev.tratamiento && <p className="text-va-body">Tratamiento: {ev.tratamiento}</p>}
          {ev.observaciones && <p className="text-va-body">Obs: {ev.observaciones}</p>}
        </div>
      ))}

      {/* Recetas */}
      {data.recetas.map((rec) => (
        <div key={rec.id} className="text-sm border-t border-va-border pt-2">
          <p className="font-medium text-va-heading">Receta</p>
          {rec.diagnostico && <p className="text-va-muted">Dx: {rec.diagnostico}</p>}
          <ul className="list-disc list-inside text-va-body">
            {rec.items.map((it, i) => (
              <li key={i}>
                {it.medicamento}
                {it.dosis && ` — ${it.dosis}`}
                {it.frecuencia && ` — ${it.frecuencia}`}
                {it.duracion && ` — ${it.duracion}`}
              </li>
            ))}
          </ul>
        </div>
      ))}

      {/* Pedidos */}
      {data.pedidos.map((ped) => (
        <div key={ped.id} className="text-sm border-t border-va-border pt-2">
          <p className="font-medium text-va-heading">Pedido ({ped.tipo})</p>
          {ped.diagnostico && <p className="text-va-muted">Dx: {ped.diagnostico}</p>}
          {ped.indicaciones && <p className="text-va-muted">Indicaciones: {ped.indicaciones}</p>}
          <ul className="list-disc list-inside text-va-body">
            {ped.items.map((it, i) => (
              <li key={i}>{it.descripcion}{it.codigo && ` (${it.codigo})`}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
