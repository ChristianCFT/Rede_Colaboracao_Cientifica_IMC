export type Pt = [number, number];

export interface GNode {
  i: number; id: string; name: string; inst: string; area: string; lat: string;
  /** grau vindo do backend */
  deg: number;
  grp: string; comp: boolean; mat: boolean;
  /** true = sem colaboração com o IMC */
  extended: boolean;
  x: number; y: number;
  lay: { free: Pt; area: Pt };
  /** índices em E */
  adj: number[];
  /** posição de repouso da física */
  ax: number; ay: number;
  // d3-force
  index?: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null;
}

export interface GEdge {
  i: number; a: number; b: number; tipo: string; vc: number[]; sum: number;
  /** 0 a 1, vem do backend */
  w: number;
  cd: number[][];
}

export type ColorMode = 'inst' | 'area';
export type LayoutMode = 'free' | 'area';
