// Tipos do modelo no cliente, compartilhados por todos os módulos.

export type Pt = [number, number];

export interface GNode {
  i: number; id: string; name: string; inst: string; area: string; lat: string;
  /** Nº de parceiros no universo do pesquisador (grau vindo do backend). */
  deg: number;
  grp: string; comp: boolean; mat: boolean;
  /** true = pesquisador sem colaboração com o IMC (só vértice, sem relações); false = rede principal. */
  extended: boolean;
  x: number; y: number;
  lay: { free: Pt; area: Pt };
  /** Índices (em E) das arestas do nó. */
  adj: number[];
  /** Posição de repouso usada pela física (layout atual ou onde o usuário soltou o nó). */
  ax: number; ay: number;
  // Campos geridos pelo d3-force.
  index?: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null;
}

export interface GEdge {
  i: number; a: number; b: number; tipo: string; vc: number[]; sum: number;
  /** Peso normalizado da relação inteira (0 a 1), vindo do backend. */
  w: number;
  /** Atividades da relação por dimensão, como índices inteiros (para filtrar rápido). */
  cd: number[][];
}

export type ColorMode = 'inst' | 'area';
export type LayoutMode = 'free' | 'area';
