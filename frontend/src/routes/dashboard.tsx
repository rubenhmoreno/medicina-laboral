import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { Card, CardBody, Badge, Button } from "@/components/ui";
import { licenciasApi, type Licencia } from "@/api/licencias";

function StatCard({ label, value, icon, color, to }: { label: string; value: string | number; icon: React.ReactNode; color: string; to?: string }) {
  const content = (
    <Card className="overflow-hidden">
      <CardBody className="flex items-center gap-4">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${color}`}>
          {icon}
        </div>
        <div>
          <p className="text-3xl font-extrabold text-va-heading">{value}</p>
          <p className="text-sm text-va-muted">{label}</p>
        </div>
      </CardBody>
    </Card>
  );
  if (to) {
    return <Link to={to} className="block transition-transform hover:scale-[1.02]">{content}</Link>;
  }
  return content;
}

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ activas: 0, pendientes: 0 });
  const [recientes, setRecientes] = useState<Licencia[]>([]);

  useEffect(() => {
    licenciasApi.count({ vigente: true }).then((n) => setStats((s) => ({ ...s, activas: n }))).catch(() => {});
    licenciasApi.count({ estado: "enviado" }).then((n) => setStats((s) => ({ ...s, pendientes: n }))).catch(() => {});
    licenciasApi.list({ limit: 15 }).then(setRecientes).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      {/* Welcome banner */}
      <div className="gradient-va rounded-xl p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold">
          Bienvenido, {user?.nombre ?? user?.email}
        </h1>
        <p className="mt-1 text-sm text-white/70">Panel de control del sistema de medicina laboral</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Licencias activas"
          value={stats.activas}
          color="bg-emerald-100 text-emerald-600"
          to="/licencias?vigente=true"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          label="Pendientes de validacion"
          value={stats.pendientes}
          color="bg-accent-100 text-accent-600"
          to="/licencias?estado=enviado"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Quick actions */}
      <Card>
        <CardBody>
          <h2 className="mb-4 text-lg font-semibold text-va-heading">Accesos rapidos</h2>
          <div className="flex flex-wrap gap-3">
            <Link to="/atenciones/nueva">
              <Button>Nueva consulta</Button>
            </Link>
            <Link to="/licencias/nueva">
              <Button>Nueva licencia</Button>
            </Link>
            <Link to="/empleados/nuevo">
              <Button variant="secondary">Nuevo empleado</Button>
            </Link>
            <Link to="/reportes">
              <Button variant="secondary">Ver reportes</Button>
            </Link>
          </div>
        </CardBody>
      </Card>

      {/* Recent */}
      {recientes.length > 0 && (
        <Card>
          <CardBody>
            <h2 className="mb-4 text-lg font-semibold text-va-heading">Actividad reciente</h2>
            <div className="space-y-2">
              {recientes.map((l) => (
                <Link
                  key={l.id}
                  to={`/licencias/${l.id}`}
                  className="flex items-center justify-between rounded-lg border border-va-border px-4 py-3 transition-default hover:bg-accent-50/30 hover:border-accent-200"
                >
                  <div className="text-sm">
                    <span className="font-medium text-va-heading">
                      {l.empleado_nombre ?? "—"}
                    </span>
                    <span className="ml-3 text-va-muted">
                      {l.fecha_desde} - {l.fecha_hasta}
                    </span>
                    <span className="ml-3 font-semibold text-va-heading">
                      {l.dias_otorgados ?? l.dias_solicitados} dias
                    </span>
                  </div>
                  <Badge>{l.estado}</Badge>
                </Link>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
