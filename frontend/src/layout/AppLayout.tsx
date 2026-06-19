import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const links = [
  { to: "/", label: "Inicio", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/empleados", label: "Empleados", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/licencias", label: "Licencias", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/reportes", label: "Reportes", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/admin/topes", label: "Topes", roles: ["admin"] as const },
  { to: "/admin/usuarios", label: "Usuarios", roles: ["admin"] as const },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <div className="min-h-screen grid grid-cols-[220px_1fr]">
      <aside className="bg-slate-900 text-slate-100 p-4 space-y-2">
        <div className="font-bold mb-4">Medicia-Laboral</div>
        {links.filter((l) => l.roles.includes(user.rol)).map((l) => (
          <NavLink key={l.to} to={l.to}
                   className={({ isActive }) =>
                     `block px-3 py-2 rounded ${isActive ? "bg-slate-700" : "hover:bg-slate-800"}`}>
            {l.label}
          </NavLink>
        ))}
        <div className="absolute bottom-4 left-4 right-4 text-xs">
          <div className="opacity-70">{user.email}</div>
          <button onClick={logout} className="mt-2 underline">Salir</button>
        </div>
      </aside>
      <main className="p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}
