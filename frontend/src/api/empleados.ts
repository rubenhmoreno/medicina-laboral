import { http } from "./http";

export type Empleado = {
  id: string; legajo: string; cuil: string;
  nombre: string; apellido: string;
  fecha_nacimiento: string | null; fecha_ingreso: string;
  area_id: string | null; categoria_id: string; supervisor_id: string | null;
  obra_social: string | null; nro_carnet: string | null;
  email: string | null; telefono: string | null; activo: boolean;
};

export type EmpleadoCreate = Omit<Empleado, "id" | "activo">;

export type EmpleadoUpdate = {
  nombre?: string; apellido?: string;
  area_id?: string | null; categoria_id?: string;
  supervisor_id?: string | null;
  obra_social?: string | null; nro_carnet?: string | null;
  email?: string | null; telefono?: string | null;
  activo?: boolean;
};

export const empleadosApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    http.get<Empleado[]>("/api/empleados", { params: { q, limit, offset } }).then((r) => r.data),
  count: () => http.get<{ count: number }>("/api/empleados/count").then((r) => r.data.count),
  get: (id: string) => http.get<Empleado>(`/api/empleados/${id}`).then((r) => r.data),
  create: (p: EmpleadoCreate) => http.post<Empleado>("/api/empleados", p).then((r) => r.data),
  update: (id: string, p: EmpleadoUpdate) => http.put<Empleado>(`/api/empleados/${id}`, p).then((r) => r.data),
};
