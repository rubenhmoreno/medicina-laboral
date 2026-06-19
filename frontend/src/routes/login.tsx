import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { Button, Input } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      nav("/");
    } catch {
      setError("Credenciales invalidas o cuenta bloqueada.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex">
      {/* Left panel — blackbox brand */}
      <div className="hidden lg:flex lg:w-1/2 gradient-va flex-col justify-between p-12 text-white">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/20 backdrop-blur-sm">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </div>
            <span className="text-lg font-bold">Medicina Laboral</span>
          </div>
        </div>
        <div>
          <h2 className="text-4xl font-extrabold leading-tight">
            Sistema de Gestion<br />
            de Ausentismo<br />
            y Licencias
          </h2>
          <p className="mt-4 text-lg text-white/70">
            Municipalidad de Villa Allende
          </p>
        </div>
        <p className="text-sm text-white/40">
          v0.1.0
        </p>
      </div>

      {/* Right panel — whitebox login */}
      <div className="flex w-full items-center justify-center bg-va-bg p-8 lg:w-1/2">
        <div className="w-full max-w-sm">
          {/* Mobile brand */}
          <div className="mb-8 text-center lg:hidden">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl gradient-va shadow-lg">
              <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-va-heading">Medicina Laboral</h1>
            <p className="text-sm text-va-muted">Villa Allende</p>
          </div>

          <div className="hidden lg:block mb-8">
            <h1 className="text-2xl font-bold text-va-heading">Iniciar sesion</h1>
            <p className="mt-1 text-sm text-va-muted">Ingrese sus credenciales para acceder al sistema</p>
          </div>

          <form
            onSubmit={onSubmit}
            className="rounded-xl border border-va-border bg-va-card p-8 shadow-lg"
          >
            <div className="space-y-5">
              <Input
                label="Usuario"
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="admin"
                autoComplete="username"
              />
              <Input
                label="Clave"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••"
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              loading={loading}
              className="mt-6 w-full"
              size="lg"
            >
              Ingresar
            </Button>
          </form>
        </div>
      </div>
    </main>
  );
}
