import { http } from "./http";

export type Area = { id: string; nombre: string; parent_id: string | null };
export type Categoria = { id: string; codigo: string; nombre: string; activa: boolean };
export type TipoLicencia = { id: string; codigo: string; nombre: string; base_legal: string | null; paga: boolean; computa_dias: boolean };
export type Diagnostico = { id: string; codigo_cie10: string | null; descripcion: string; categoria: string | null; requiere_junta: boolean };

export const catalogosApi = {
  areas: () => http.get<Area[]>("/api/areas").then((r) => r.data),
  categorias: () => http.get<Categoria[]>("/api/categorias").then((r) => r.data),
  tiposLicencia: () => http.get<TipoLicencia[]>("/api/tipos-licencia").then((r) => r.data),
  diagnosticos: () => http.get<Diagnostico[]>("/api/diagnosticos").then((r) => r.data),
};
