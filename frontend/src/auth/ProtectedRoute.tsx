import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({ roles }: { roles?: Array<"admin"|"medico"|"rrhh"> }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="p-6">Cargando…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.rol)) return <Navigate to="/" replace />;
  return <Outlet />;
}
