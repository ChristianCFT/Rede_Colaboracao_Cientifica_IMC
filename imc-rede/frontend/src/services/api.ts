import type { GraphDTO, GraphFilterParams, NodeDetailDTO } from '../types/graph';

const BASE: string = import.meta.env.VITE_API_URL ?? '/api/v1';

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'ApiError'; }
}

type Query = Record<string, string | number | boolean | string[] | undefined>;

async function get<T>(path: string, params: Query = {}): Promise<T> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined) continue;
    (Array.isArray(v) ? v : [v]).forEach((x) => q.append(k, String(x)));
  }
  let r: Response;
  try { r = await fetch(`${BASE}${path}${q.size ? `?${q}` : ''}`); }
  catch { throw new ApiError(0, 'Não foi possível conectar à API. O backend está rodando em http://127.0.0.1:8000?'); }
  if (!r.ok) {
    const body = (await r.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(r.status, body.detail ?? r.statusText);
  }
  return (await r.json()) as T;
}

export const api = {
  graph: (): Promise<GraphDTO> => get<GraphDTO>('/graph'),
  filter: (f: GraphFilterParams): Promise<GraphDTO> => get<GraphDTO>('/graph/filter', { ...f }),
  node: (id: string): Promise<NodeDetailDTO> => get<NodeDetailDTO>(`/nodes/${encodeURIComponent(id)}`),
  exportUrl: (fmt: 'gexf' | 'graphml'): string => `${BASE}/export/${fmt}`,
};
