import { http } from "./http";

export type Tope = {
  id: string; categoria_id: string; tipo_licencia_id: string;
  dias_maximos: number; ventana: "anio-calendario" | "anio-aniversario" | "sin-limite";
  vigente_desde: string; vigente_hasta: string | null; observacion: string | null;
};

export const topesApi = {
  list: () => http.get<Tope[]>("/api/admin/topes").then((r) => r.data),
  set: (categoria_id: string, tipo_licencia_id: string, body: { dias_maximos: number; ventana: string; desde: string; observacion?: string }) =>
    http.put<Tope>(`/api/admin/topes/${categoria_id}/${tipo_licencia_id}`, body).then((r) => r.data),
};
