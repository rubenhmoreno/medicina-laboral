import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { http } from "@/api/http";
import { useAuth } from "@/auth/AuthContext";
import { Badge, Button, Input, PageHeader, Select, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

type Atencion = {
  id: string; empleado_id: string; asignado_por: string;
  medico_id: string | null; fecha_turno: string; motivo: string;
  estado: string; notas_medicas: string | null;
  created_at: string; updated_at: string;
  empleado_nombre?: string | null;
  empleado_legajo?: string | null;
  medico_nombre?: string | null;
};

const ESTADO_COLORS: Record<string, "amber" | "green" | "red"> = {
  pendiente: "amber",
  completada: "green",
  cancelada: "red",
};

export function AtencionesListPage() {
  const { user } = useAuth();
  const [rows, setRows] = useState<Atencion[]>([]);
  const [loading, setLoading] = useState(true);
  const [estado, setEstado] = useState("");
  const [fecha, setFecha] = useState("");

  async function reload() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (estado) params.estado = estado;
      if (fecha) params.fecha = fecha;
      const { data } = await http.get<Atencion[]>("/api/atenciones", { params });
      setRows(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [estado, fecha]);

  const canCreate = user && (user.rol === "admin" || user.rol === "rrhh" || user.rol === "medico");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Atenciones"
        subtitle="Turnos medicos y atenciones"
        actions={
          canCreate ? (
            <Link to="/atenciones/nueva">
              <Button>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Nuevo turno
              </Button>
            </Link>
          ) : undefined
        }
      />

      <div className="flex flex-wrap gap-4">
        <Select
          label="Estado"
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
          placeholder="Todos"
        >
          <option value="pendiente">Pendiente</option>
          <option value="completada">Completada</option>
          <option value="cancelada">Cancelada</option>
        </Select>
        <Input
          label="Fecha"
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
        />
        {(estado || fecha) && (
          <div className="flex items-end">
            <Button variant="ghost" onClick={() => { setEstado(""); setFecha(""); }}>
              Limpiar filtros
            </Button>
          </div>
        )}
      </div>

      <Table>
        <THead>
          <tr>
            <TH>Fecha turno</TH>
            <TH>Paciente</TH>
            <TH>Motivo</TH>
            <TH>Estado</TH>
            <TH className="w-24">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((a) => (
            <TR key={a.id}>
              <TD className="font-semibold text-va-heading">
                {new Date(a.fecha_turno).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" })}
              </TD>
              <TD className="font-medium text-va-heading">{a.empleado_nombre ?? "—"}</TD>
              <TD className="max-w-xs truncate">{a.motivo}</TD>
              <TD>
                <Badge variant={ESTADO_COLORS[a.estado]}>{a.estado}</Badge>
              </TD>
              <TD>
                <Link to={`/atenciones/${a.id}`} className="text-sm text-accent-600 hover:underline">
                  Ver
                </Link>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
