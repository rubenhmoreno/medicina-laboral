import { http } from "./http";

export type Adjunto = {
  id: string; licencia_id: string; nombre_original: string; mime_type: string;
  size_bytes: number; sha256: string; created_at: string;
};

export const adjuntosApi = {
  upload: (licencia_id: string, file: File) => {
    const fd = new FormData();
    fd.append("licencia_id", licencia_id);
    fd.append("file", file);
    return http.post<Adjunto>("/api/adjuntos", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  downloadUrl: (id: string) => http.get<{ url: string; expires_in_seconds: number }>(`/api/adjuntos/${id}/download`).then((r) => r.data),
};
