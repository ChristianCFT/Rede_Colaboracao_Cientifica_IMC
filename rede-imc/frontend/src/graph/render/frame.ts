// destaque: nó em foco, vizinhos e arestas entre eles; o resto fica apagado
import { E, N } from '../../core/model';
import { selection } from '../../core/state';
import type { View } from '../../core/selectors';
import type { GEdge } from '../../core/types';

export interface Theme { tx: string; bg: string }

export interface Focus {
  active: boolean;
  hover: boolean;
  node: number;
  edge: number;
  /** 1 = em foco */
  near: Uint8Array;
}

export interface Frame {
  ctx: CanvasRenderingContext2D;
  W: number;
  H: number;
  view: View;
  focus: Focus;
  theme: Theme;
  r: number;
}

let near = new Uint8Array(0);

export function computeFocus(v: View): Focus {
  if (near.length !== N.length) near = new Uint8Array(N.length); else near.fill(0);
  let node = -1, edge = -1;
  const hover = selection.hover >= 0 && v.nOn[selection.hover] === 1;
  if (hover) node = selection.hover;
  else if (selection.node >= 0 && v.nOn[selection.node]) node = selection.node;
  else if (selection.edge >= 0 && v.eOn[selection.edge]) edge = selection.edge;
  if (node >= 0) { near[node] = 1; for (const j of N[node]!.adj) if (v.eOn[j]) { near[E[j]!.a] = 1; near[E[j]!.b] = 1; } }
  if (edge >= 0) { near[E[edge]!.a] = 1; near[E[edge]!.b] = 1; }
  return { active: node >= 0 || edge >= 0, hover, node, edge, near };
}

export const isHighlighted = (f: Focus, e: GEdge): boolean =>
  (f.node >= 0 && (e.a === f.node || e.b === f.node)) || e.i === f.edge;
