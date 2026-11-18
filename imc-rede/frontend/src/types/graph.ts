// ---- Contratos da API (espelham backend/app/schemas/graph.py) ----
export interface Producao { art: number; prj: number; ori: number; ban: number; ptt: number }
export interface NodeDTO {
  id: string; label: string; instituto: string; area: string; grupo: string; comp: boolean; mat: boolean;
  grau: number; centralidade_grau: number; intermediacao: number; lattes_url: string; observacao: string;
  producao: Producao | null; x: number; y: number; x_area: number; y_area: number;
}
export interface EdgeDTO {
  source: string; target: string; tipo_relacao: string; escopo: string; area_imc: string;
  vetor_contagem: number[]; vetor_bruto: string[][]; soma_bruta: number;
}
export interface AtividadeDTO { ano: string; titulo: string }
export interface MetricsDTO { nos: number; arestas: number; densidade: number; grau_medio: number; componentes: number }
export interface GraphDTO {
  nodes: NodeDTO[]; edges: EdgeDTO[]; atividades: Record<string, AtividadeDTO>;
  areas: { nome: string; cor: string; total: number }[];
  paleta: Record<string, string>; cores_grupo: Record<string, string>; dimensoes: string[]; metricas: MetricsDTO;
}
export interface NodeDetailDTO extends NodeDTO {
  vizinhos: { id: string; label: string; instituto: string; tipo_relacao: string; soma_bruta: number;
              vetor_contagem: number[]; atividades: (AtividadeDTO & { id: string; dimensao: string })[] }[];
}
export interface GraphFilterParams {
  grupos?: string[]; tipos?: string[]; peso_min?: number; centralidade_min?: number; incluir_externos?: boolean;
}

// ---- Modelo de cliente ----
export type Pt = [number, number];
export interface GNode {
  i: number; id: string; name: string; inst: string; area: string; deg: number; x: number; y: number; lat: string;
  prod: number[] | null; obs: string; grp: string; comp: boolean; mat: boolean; cen: number; btw: number;
  lay: { free: Pt; area: Pt }; adj: number[];
  /** Posição de repouso usada pela física (layout atual ou onde o usuário soltou o nó). */
  ax: number; ay: number;
  // Campos geridos pelo d3-force.
  index?: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null;
}
export interface GEdge {
  i: number; a: number; b: number; tipo: string; vc: number[]; vb: string[][]; sum: number;
  /** Mesmo conteúdo de vb, mas com índices inteiros de atividade (para filtrar rápido). */
  cd: number[][];
}
export type ColorMode = 'inst' | 'area';
export type LayoutMode = 'free' | 'area';
export type SizeMetric = 'deg' | 'vol' | 'btw';
export interface UIState {
  W: number; H: number; dpr: number; k: number; tx: number; ty: number; sel: number; selE: number; hov: number;
  minS: number; showLab: boolean; showExt: boolean; colorMode: ColorMode; layoutMode: LayoutMode;
  sizeMetric: SizeMetric; y0: number; y1: number; ego: boolean; physics: boolean;
}
