import { http } from "./http";

export type Empleado = {
  id: string; legajo: string; cuil: string;
  nombre: string; apellido: string;
  fecha_nacimiento: string | null; fecha_ingreso: string;
  area_id: string | null; categoria_id: string; supervisor_id: string | null;
  email: string | null; telefono: string | null; activo: boolean;
};

export type EmpleadoCreate = Omit<Empleado, "id" | "activo">;

export const empleadosApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    http.get<Empleado[]>("/api/empleados", { params: { q, limit, offset } }).then((r) => r.data),
  get: (id: string) => http.get<Empleado>(`/api/empleados/${id}`).then((r) => r.data),
  create: (p: EmpleadoCreate) => http.post<Empleado>("/api/empleados", p).then((r) => r.data),
};
