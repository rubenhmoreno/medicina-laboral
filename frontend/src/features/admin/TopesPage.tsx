import { useEffect, useState } from "react";
import { catalogosApi, type Categoria, type TipoLicencia } from "@/api/catalogos";
import { topesApi, type Tope } from "@/api/topes";

const VENTANAS = ["anio-calendario", "anio-aniversario", "sin-limite"] as const;

export function TopesPage() {
  const [cats, setCats] = useState<Categoria[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [topes, setTopes] = useState<Tope[]>([]);

  async function reload() {
    setCats(await catalogosApi.categorias());
    setTipos(await catalogosApi.tiposLicencia());
    setTopes(await topesApi.list());
  }
  useEffect(() => { reload(); }, []);

  function topeFor(catId: string, tipoId: string) {
    return topes.find((t) => t.categoria_id === catId && t.tipo_licencia_id === tipoId);
  }

  async function update(catId: string, tipoId: string) {
    const dias = parseInt(prompt("Días máximos:") ?? "", 10);
    if (!Number.isFinite(dias) || dias < 0) return;
    const ventana = (prompt(`Ventana (${VENTANAS.join("/")})`) ?? "anio-calendario") as string;
    if (!VENTANAS.includes(ventana as any)) return;
    const desde = prompt("Vigente desde (YYYY-MM-DD):", new Date().toISOString().slice(0, 10)) ?? "";
    await topesApi.set(catId, tipoId, { dias_maximos: dias, ventana, desde });
    await reload();
  }

  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Topes de días (admin)</h1>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead>
          <tr className="bg-slate-100">
            <th className="p-2 text-left">Categoría \ Tipo licencia</th>
            {tipos.map((t) => <th key={t.id} className="p-2">{t.nombre}</th>)}
          </tr>
        </thead>
        <tbody>
          {cats.map((c) => (
            <tr key={c.id} className="border-t">
              <td className="p-2 font-medium">{c.nombre}</td>
              {tipos.map((t) => {
                const found = topeFor(c.id, t.id);
                return (
                  <td key={t.id} className="p-2">
                    <button onClick={() => update(c.id, t.id)} className="underline">
                      {found ? `${found.dias_maximos} (${found.ventana})` : "—"}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
