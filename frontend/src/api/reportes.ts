import { http } from "./http";

export const reportesApi = {
  porArea: (desde: string, hasta: string) =>
    http.get("/api/reportes/por-area", { params: { desde, hasta } }).then((r) => r.data),
  porCategoriaDiag: (desde: string, hasta: string) =>
    http.get("/api/reportes/por-categoria-diag", { params: { desde, hasta } }).then((r) => r.data),
  mensual: (desde: string, hasta: string) =>
    http.get("/api/reportes/mensual", { params: { desde, hasta } }).then((r) => r.data),
  downloadCsv: (path: string, desde: string, hasta: string) => {
    const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
    window.location.href = `${base}/api/reportes/${path}?desde=${desde}&hasta=${hasta}&formato=csv`;
  },
};
