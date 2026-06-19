import { http } from "./http";

export type Area = { id: string; nombre: string; parent_id: string | null };
export type Categoria = { id: string; codigo: string; nombre: string; activa: boolean };
export type TipoLicencia = { id: string; codigo: string; nombre: string; base_legal: string | null; paga: boolean; computa_dias: boolean };

export const catalogosApi = {
  areas: () => http.get<Area[]>("/api/areas").then((r) => r.data),
  categorias: () => http.get<Categoria[]>("/api/categorias").then((r) => r.data),
  tiposLicencia: () => http.get<TipoLicencia[]>("/api/tipos-licencia").then((r) => r.data),
};
