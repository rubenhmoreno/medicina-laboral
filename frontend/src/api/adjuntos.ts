import { http } from "./http";

export type Adjunto = {
  id: string; licencia_id: string | null; atencion_id: string | null;
  nombre_original: string; mime_type: string;
  size_bytes: number; sha256: string; created_at: string;
};

export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

export function validateFiles(files: File[]): string | null {
  for (const f of files) {
    if (f.size > MAX_FILE_SIZE) {
      return `El archivo "${f.name}" supera el limite de 5 MB (${(f.size / 1024 / 1024).toFixed(1)} MB)`;
    }
  }
  return null;
}

export const adjuntosApi = {
  upload: (file: File, opts: { licencia_id?: string; atencion_id?: string }) => {
    const fd = new FormData();
    if (opts.licencia_id) fd.append("licencia_id", opts.licencia_id);
    if (opts.atencion_id) fd.append("atencion_id", opts.atencion_id);
    fd.append("file", file);
    return http.post<Adjunto>("/api/adjuntos", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  uploadMany: async (files: File[], opts: { licencia_id?: string; atencion_id?: string }) => {
    const results: Adjunto[] = [];
    for (const file of files) {
      results.push(await adjuntosApi.upload(file, opts));
    }
    return results;
  },
  downloadUrl: (id: string) => http.get<{ url: string; expires_in_seconds: number }>(`/api/adjuntos/${id}/download`).then((r) => r.data),
};
