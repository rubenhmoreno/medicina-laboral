import { useEffect, useState } from "react";
import { http } from "@/api/http";
import { Button, Card, CardBody, Input, PageHeader } from "@/components/ui";

type ConfigItem = {
  id: string;
  clave: string;
  valor: string;
  descripcion: string | null;
};

const LABELS: Record<string, string> = {
  pdf_header_linea1: "Encabezado - Linea 1",
  pdf_header_linea2: "Encabezado - Linea 2",
  pdf_header_linea3: "Encabezado - Linea 3 (direccion/telefono)",
  pdf_footer: "Pie de pagina",
};

export function ConfiguracionPage() {
  const [items, setItems] = useState<ConfigItem[]>([]);
  const [edited, setEdited] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get<ConfigItem[]>("/api/configuracion");
      setItems(data);
      setEdited({});
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  function handleChange(clave: string, valor: string) {
    setEdited((prev) => ({ ...prev, [clave]: valor }));
    setSaved(false);
  }

  const hasChanges = Object.keys(edited).some((k) => {
    const original = items.find((i) => i.clave === k);
    return original && original.valor !== edited[k];
  });

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    try {
      const promises = Object.entries(edited)
        .filter(([k, v]) => {
          const original = items.find((i) => i.clave === k);
          return original && original.valor !== v;
        })
        .map(([clave, valor]) => http.put(`/api/configuracion/${clave}`, { valor }));
      await Promise.all(promises);
      await reload();
      setSaved(true);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message ?? "Error al guardar configuracion");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="p-6 text-va-muted">Cargando configuracion...</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Configuracion"
        subtitle="Parametros generales del sistema (encabezados y pies de pagina de documentos)"
      />

      <Card>
        <CardBody className="space-y-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-va-heading">
            Encabezado y pie de pagina de documentos
          </h3>
          <p className="text-sm text-va-muted">
            Estos valores se utilizan en la impresion de recetas, pedidos medicos y el PDF de historia clinica.
          </p>

          <div className="space-y-4">
            {items.map((item) => (
              <Input
                key={item.clave}
                label={LABELS[item.clave] ?? item.clave}
                value={edited[item.clave] ?? item.valor}
                onChange={(e) => handleChange(item.clave, e.target.value)}
                helper={item.descripcion ?? undefined}
              />
            ))}
          </div>

          <div className="flex items-center gap-4 pt-2">
            <Button onClick={handleSave} loading={saving} disabled={!hasChanges}>
              Guardar cambios
            </Button>
            {saved && (
              <span className="text-sm text-green-600 font-medium">Configuracion guardada</span>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
