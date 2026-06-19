import { useAuth } from "@/auth/AuthContext";

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Bienvenido, {user?.nombre ?? user?.email}</h1>
      <p className="text-slate-600">Rol: {user?.rol}</p>
    </section>
  );
}
