import { useEffect, useState } from "react";
import { catalogosApi, type Categoria, type TipoLicencia } from "@/api/catalogos";
import { topesApi, type Tope } from "@/api/topes";
import { Button, Input, Select, Modal, PageHeader, Table, THead, TBody, TH, TD, TR } from "@/components/ui";

const VENTANAS = ["anio-calendario", "anio-aniversario", "sin-limite"] as const;

const ventanaLabels: Record<string, string> = {
  "anio-calendario": "Ano calendario",
  "anio-aniversario": "Ano aniversario",
  "sin-limite": "Sin limite",
};

export function TopesPage() {
  const [cats, setCats] = useState<Categoria[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [topes, setTopes] = useState<Tope[]>([]);
  const [modal, setModal] = useState<{ catId: string; tipoId: string } | null>(null);
  const [dias, setDias] = useState("");
  const [ventana, setVentana] = useState<string>("anio-calendario");
  const [desde, setDesde] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);

  async function reload() {
    setCats(await catalogosApi.categorias());
    setTipos(await catalogosApi.tiposLicencia());
    setTopes(await topesApi.list());
  }
  useEffect(() => { reload(); }, []);

  function topeFor(catId: string, tipoId: string) {
    return topes.find((t) => t.categoria_id === catId && t.tipo_licencia_id === tipoId);
  }

  function openEdit(catId: string, tipoId: string) {
    const existing = topeFor(catId, tipoId);
    setDias(existing ? String(existing.dias_maximos) : "");
    setVentana(existing?.ventana ?? "anio-calendario");
    setDesde(new Date().toISOString().slice(0, 10));
    setModal({ catId, tipoId });
  }

  async function handleSave() {
    if (!modal) return;
    const d = parseInt(dias, 10);
    if (!Number.isFinite(d) || d < 0) return;
    setLoading(true);
    try {
      await topesApi.set(modal.catId, modal.tipoId, { dias_maximos: d, ventana, desde });
      setModal(null);
      await reload();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Topes de dias"
        subtitle="Configure los limites de dias por categoria y tipo de licencia"
      />

      <Table>
        <THead>
          <tr>
            <TH>Categoria</TH>
            {tipos.map((t) => (
              <TH key={t.id} className="text-center">{t.nombre}</TH>
            ))}
          </tr>
        </THead>
        <TBody empty={cats.length === 0}>
          {cats.map((c) => (
            <TR key={c.id}>
              <TD className="font-semibold text-va-heading">{c.nombre}</TD>
              {tipos.map((t) => {
                const found = topeFor(c.id, t.id);
                return (
                  <TD key={t.id} className="text-center">
                    <button
                      onClick={() => openEdit(c.id, t.id)}
                      className={`rounded-lg px-3 py-1.5 text-sm transition-default ${
                        found
                          ? "bg-accent-50 text-primary-700 hover:bg-accent-100 font-medium border border-accent-200"
                          : "text-va-muted hover:bg-slate-100 hover:text-va-body"
                      }`}
                    >
                      {found ? (
                        <span>{found.dias_maximos}d / {ventanaLabels[found.ventana] || found.ventana}</span>
                      ) : (
                        <span>—</span>
                      )}
                    </button>
                  </TD>
                );
              })}
            </TR>
          ))}
        </TBody>
      </Table>

      {/* Edit Modal */}
      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title="Configurar tope"
        actions={
          <>
            <Button variant="secondary" onClick={() => setModal(null)}>Cancelar</Button>
            <Button onClick={handleSave} loading={loading}>Guardar</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Dias maximos"
            type="number"
            value={dias}
            onChange={(e) => setDias(e.target.value)}
            min={0}
            required
          />
          <Select
            label="Ventana"
            value={ventana}
            onChange={(e) => setVentana(e.target.value)}
          >
            {VENTANAS.map((v) => (
              <option key={v} value={v}>{ventanaLabels[v]}</option>
            ))}
          </Select>
          <Input
            label="Vigente desde"
            type="date"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
            required
          />
        </div>
      </Modal>
    </div>
  );
}
