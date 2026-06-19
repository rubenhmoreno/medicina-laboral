import { http } from "./http";

export type EstadoLicencia = "borrador" | "enviado" | "validado" | "rechazado" | "anulado";
export type OrigenLicencia = "rrhh" | "medico";

export type Licencia = {
  id: string; empleado_id: string; tipo_licencia_id: string;
  diagnostico_id: string | null;
  fecha_desde: string; fecha_hasta: string;
  dias_solicitados: number; dias_otorgados: number | null;
  estado: EstadoLicencia; origen: OrigenLicencia;
  observaciones: string | null; motivo_rechazo: string | null; motivo_anulacion: string | null;
  certificante: string | null; matricula_certificante: string | null;
  creado_por: string; validado_por: string | null; validado_en: string | null;
};

export type LicenciaCreate = {
  empleado_id: string; tipo_licencia_id: string; diagnostico_id?: string | null;
  fecha_desde: string; fecha_hasta: string;
  observaciones?: string | null; certificante?: string | null; matricula_certificante?: string | null;
};

export const licenciasApi = {
  list: (params: { estado?: EstadoLicencia; empleado_id?: string; area_id?: string; desde?: string; hasta?: string; limit?: number; offset?: number }) =>
    http.get<Licencia[]>("/api/licencias", { params }).then((r) => r.data),
  get: (id: string) => http.get<Licencia>(`/api/licencias/${id}`).then((r) => r.data),
  create: (p: LicenciaCreate) => http.post<Licencia>("/api/licencias", p).then((r) => r.data),
  enviar: (id: string) => http.post<Licencia>(`/api/licencias/${id}/enviar`).then((r) => r.data),
  validar: (id: string, dias_otorgados: number, observaciones?: string) =>
    http.post<Licencia>(`/api/licencias/${id}/validar`, { dias_otorgados, observaciones }).then((r) => r.data),
  rechazar: (id: string, motivo_rechazo: string) =>
    http.post<Licencia>(`/api/licencias/${id}/rechazar`, { motivo_rechazo }).then((r) => r.data),
  anular: (id: string, motivo_anulacion: string) =>
    http.post<Licencia>(`/api/licencias/${id}/anular`, { motivo_anulacion }).then((r) => r.data),
  evaluarTope: (id: string) => http.get(`/api/licencias/${id}/tope`).then((r) => r.data),
};
