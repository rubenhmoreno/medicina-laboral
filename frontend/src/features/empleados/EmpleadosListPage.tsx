import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { empleadosApi, type Empleado } from "@/api/empleados";
import { Badge, Button, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

export function EmpleadosListPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Empleado[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      empleadosApi.list(q).then(setRows).finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Empleados"
        subtitle="Gestion del padron de empleados"
        actions={
          <Link to="/empleados/nuevo">
            <Button>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Nuevo empleado
            </Button>
          </Link>
        }
      />

      <div className="max-w-md">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-va-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            className="block w-full rounded-lg border border-va-border bg-va-card py-2.5 pl-10 pr-3 text-sm shadow-sm transition-default placeholder:text-va-muted focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
            placeholder="Buscar por legajo, CUIL o nombre..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      <Table>
        <THead>
          <tr>
            <TH>Legajo</TH>
            <TH>Apellido y nombre</TH>
            <TH>CUIL</TH>
            <TH>Estado</TH>
            <TH className="w-40">Acciones</TH>
          </tr>
        </THead>
        <TBody empty={!loading && rows.length === 0}>
          {rows.map((e) => (
            <TR key={e.id}>
              <TD className="font-semibold text-va-heading">{e.legajo}</TD>
              <TD>{e.apellido}, {e.nombre}</TD>
              <TD className="font-mono text-xs">{e.cuil}</TD>
              <TD>
                <Badge>{e.activo ? "activo" : "inactivo"}</Badge>
              </TD>
              <TD>
                <div className="flex gap-3">
                  <Link to={`/empleados/${e.id}/editar`} className="text-sm text-accent-600 hover:underline">
                    Editar
                  </Link>
                  <Link to={`/empleados/${e.id}/historia-clinica`} className="text-sm text-accent-600 hover:underline">
                    Historia clinica
                  </Link>
                </div>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
