// Comunicação com o backend e contratos da API (espelham backend/src/schemas/graph_schema.py).

export interface NodeDTO {
  id: string; label: string; instituto: string; area: string; grupo: string; comp: boolean; mat: boolean;
  grau: number; lattes_url: string;
  x: number; y: number; x_area: number; y_area: number;
}
export interface EdgeDTO {
  source: string; target: string; tipo_relacao: string;
  vetor_contagem: number[]; vetor_bruto: string[][]; soma_bruta: number;
  /** Peso normalizado da colaboração (0 a 1), com todas as atividades da dupla. */
  peso: number;
}
/** Parâmetros para recalcular o peso no recorte: α e maior contagem de cada dimensão na rede. */
export interface PesoDTO { alfas: number[]; referencias: number[] }
export interface AtividadeDTO { ano: string; titulo: string }
export interface GraphDTO {
  nodes: NodeDTO[]; edges: EdgeDTO[];
  /** Pesquisadores sem colaboração direta com o IMC: só vértices, sem relações. */
  sem_colaboracao: NodeDTO[];
  atividades: Record<string, AtividadeDTO>;
  paleta: Record<string, string>; cores_grupo: Record<string, string>; dimensoes: string[];
  peso: PesoDTO;
}
export interface NodeDetailDTO extends NodeDTO {
  vizinhos: { id: string; label: string; instituto: string; tipo_relacao: string; soma_bruta: number; peso: number;
              vetor_contagem: number[]; atividades: (AtividadeDTO & { id: string; dimensao: string })[] }[];
}

const BASE: string = import.meta.env.VITE_API_URL ?? '/api/v1';

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'ApiError'; }
}

async function get<T>(path: string): Promise<T> {
  let r: Response;
  try { r = await fetch(`${BASE}${path}`); }
  catch { throw new ApiError(0, 'Não foi possível conectar à API. O backend está rodando em http://127.0.0.1:8000?'); }
  if (!r.ok) {
    const body = (await r.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(r.status, body.detail ?? r.statusText);
  }
  return (await r.json()) as T;
}

export const api = {
  graph: (): Promise<GraphDTO> => get<GraphDTO>('/graph'),
  node: (id: string): Promise<NodeDetailDTO> => get<NodeDetailDTO>(`/nodes/${encodeURIComponent(id)}`),
};
