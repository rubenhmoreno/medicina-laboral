// frontend/src/features/licencias/LicenciaDetailPage.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { licenciasApi, type Licencia } from "@/api/licencias";
import { useAuth } from "@/auth/AuthContext";

export function LicenciaDetailPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const [lic, setLic] = useState<Licencia | null>(null);
  const [tope, setTope] = useState<any | null>(null);

  async function reload() {
    setLic(await licenciasApi.get(id));
    try { setTope(await licenciasApi.evaluarTope(id)); } catch { setTope(null); }
  }
  useEffect(() => { reload(); }, [id]);

  if (!lic) return <p>Cargando…</p>;
  return (
    <section className="space-y-3 max-w-2xl">
      <h1 className="text-2xl font-semibold">Licencia</h1>
      <div className="bg-white rounded shadow p-4 space-y-2">
        <p><b>Estado:</b> {lic.estado}</p>
        <p><b>Desde:</b> {lic.fecha_desde} — <b>Hasta:</b> {lic.fecha_hasta}</p>
        <p><b>Días solicitados:</b> {lic.dias_solicitados} — <b>Otorgados:</b> {lic.dias_otorgados ?? "—"}</p>
        {tope && tope.tope_aplicable !== null && (
          <p className={tope.excede ? "text-red-600 font-medium" : "text-slate-600"}>
            Tope: {tope.dias_consumidos_ventana}/{tope.tope_aplicable} días en ventana. {tope.warning_msg}
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {lic.estado === "borrador" && (
          <button onClick={async () => { await licenciasApi.enviar(lic.id); await reload(); }}
                  className="bg-slate-900 text-white px-3 py-2 rounded">Enviar</button>
        )}
        {lic.estado === "enviado" && user?.rol === "medico" && (
          <>
            <button onClick={async () => {
              const d = parseInt(prompt("Días a otorgar:", String(lic.dias_solicitados)) ?? "0", 10);
              if (Number.isFinite(d)) { await licenciasApi.validar(lic.id, d); await reload(); }
            }} className="bg-emerald-700 text-white px-3 py-2 rounded">Validar</button>
            <button onClick={async () => {
              const m = prompt("Motivo de rechazo:") ?? "";
              if (m) { await licenciasApi.rechazar(lic.id, m); await reload(); }
            }} className="bg-red-700 text-white px-3 py-2 rounded">Rechazar</button>
          </>
        )}
        {lic.estado === "validado" && user?.rol === "admin" && (
          <button onClick={async () => {
            const m = prompt("Motivo de anulación:") ?? "";
            if (m) { await licenciasApi.anular(lic.id, m); await reload(); }
          }} className="bg-amber-700 text-white px-3 py-2 rounded">Anular</button>
        )}
      </div>
    </section>
  );
}
