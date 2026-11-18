// Recorte da rede (dados filtrados), memoizado pela versão dos filtros: arestas e nós ativos, pesos
// por aresta, contadores das facetas e indicadores. Hover, câmera, rótulos e física não invalidam nada.
//
// Pesquisadores sem colaboração com o IMC: são só vértices (sem arestas). Aparecem sempre que a opção
// "Incluir pesquisadores sem colaboração com o IMC" estiver marcada, e não entram em facetas nem
// indicadores, que contam apenas a rede principal.
import { CODE_DIM, CODE_YEAR, E, N, NCODES } from './model';
import { extended, filterVer, filters, fullYearRange, passesArea } from './state';

export interface Facets {
  types: Record<string, number>;
  groups: Record<string, number>;
  dims: number[];
  /** Atividades distintas na janela temporal. */
  win: number;
}

/** Indicadores da rede principal no recorte (não incluem a rede ampliada). */
export interface MainStats {
  nodes: number;
  edges: number;
  avgDegree: number;
  /** Atividades distintas por dimensão. */
  dimActivities: number[];
  totalActivities: number;
}

export interface View {
  ver: number;
  /** Atividade passa na janela temporal (independe das dimensões). */
  inWin: Uint8Array;
  /** Atividade passa na janela temporal E na sua dimensão estar ativa. */
  ok: Uint8Array;
  /** Atividades em comum por aresta no recorte (espessura, ordenação e "mín. de atividades"). */
  fsum: Int32Array;
  eOn: Uint8Array;
  nOn: Uint8Array;
  /** Nº de parceiros visíveis por nó. */
  deg: Int32Array;
  /** Atividades distintas visíveis por nó. */
  vol: Int32Array;
  /** Contadores das facetas (cada faceta ignora o próprio filtro, como numa busca facetada). */
  facets: Facets;
  stats: MainStats;
}

const groupsOf = (i: number): string[] => {
  const n = N[i]!;
  if (n.inst !== 'IMC') return [];
  const g: string[] = [];
  if (n.comp) g.push('Computação');
  if (n.mat) g.push('Matemática');
  if (!n.comp && !n.mat) g.push('Outras');
  return g;
};

function activityMasks(): { inWin: Uint8Array; ok: Uint8Array } {
  const full = fullYearRange();
  const inWin = new Uint8Array(NCODES), ok = new Uint8Array(NCODES);
  for (let c = 0; c < NCODES; c++) {
    const y = CODE_YEAR[c]!;
    const w = full || (y > 0 && y >= filters.yearFrom && y <= filters.yearTo);
    inWin[c] = w ? 1 : 0;
    ok[c] = w && filters.dims[CODE_DIM[c]!] ? 1 : 0;
  }
  return { inWin, ok };
}

function filterEdges(inWin: Uint8Array, ok: Uint8Array): { fsum: Int32Array; eOn: Uint8Array; facets: Facets } {
  const m = E.length;
  const fsum = new Int32Array(m), eOn = new Uint8Array(m);
  const types: Record<string, number> = {};
  Object.keys(filters.types).forEach((t) => { types[t] = 0; });
  const groupMark = new Uint8Array(N.length);
  const dimStamp = new Uint8Array(NCODES), winStamp = new Uint8Array(NCODES);
  const dims = [0, 0, 0, 0, 0];
  let win = 0;

  for (let e = 0; e < m; e++) {
    const ed = E[e]!, a = N[ed.a]!, b = N[ed.b]!;
    let s = 0;
    for (let j = 0; j < 5; j++) {
      if (!filters.dims[j]) continue;
      for (const k of ed.cd[j]!) s += ok[k]!;
    }
    fsum[e] = s;
    const pT = filters.types[ed.tipo] ?? true;
    const pA = passesArea(a) && passesArea(b);
    const pX = filters.showExternal || (a.inst !== 'EXT' && b.inst !== 'EXT');
    const pW = s > 0 && s >= filters.minActivities;
    if (pT && pA && pX && pW) eOn[e] = 1;
    if (pA && pX && pW) types[ed.tipo] = (types[ed.tipo] ?? 0) + 1;
    if (pT && pX && pW) { groupMark[ed.a] = 1; groupMark[ed.b] = 1; }
    if (pT && pA && pX) {
      for (let j = 0; j < 5; j++) {
        for (const k of ed.cd[j]!) {
          if (!inWin[k]) continue;
          if (!dimStamp[k]) { dimStamp[k] = 1; dims[j]!++; }
          if (!winStamp[k]) { winStamp[k] = 1; win++; }
        }
      }
    }
  }

  const groups: Record<string, number> = {};
  Object.keys(filters.groups).forEach((g) => { groups[g] = 0; });
  groupMark.forEach((v, i) => { if (v) groupsOf(i).forEach((g) => { groups[g] = (groups[g] ?? 0) + 1; }); });
  return { fsum, eOn, facets: { types, groups, dims, win } };
}

function filterNodes(eOn: Uint8Array): Uint8Array {
  const nOn = new Uint8Array(N.length);
  for (let i = 0; i < N.length; i++) {
    const n = N[i]!;
    if (n.inst === 'EXT' && !filters.showExternal) nOn[i] = 0;
    else if (n.extended) nOn[i] = extended.visible ? 1 : 0;
    else if (n.inst === 'IMC') nOn[i] = passesArea(n) ? 1 : 0;
    else nOn[i] = n.adj.some((j) => eOn[j] === 1) ? 1 : 0;
  }
  return nOn;
}

function nodeTotals(eOn: Uint8Array, nOn: Uint8Array, ok: Uint8Array): { deg: Int32Array; vol: Int32Array } {
  const deg = new Int32Array(N.length);
  for (let j = 0; j < E.length; j++) if (eOn[j]) { deg[E[j]!.a]!++; deg[E[j]!.b]!++; }
  // Atividades distintas por nó (marcação com "carimbo" para evitar Sets).
  const vol = new Int32Array(N.length);
  const stamp = new Int32Array(NCODES).fill(-1);
  for (let i = 0; i < N.length; i++) {
    if (!nOn[i]) continue;
    let c = 0;
    for (const j of N[i]!.adj) {
      if (!eOn[j]) continue;
      for (const arr of E[j]!.cd) for (const k of arr) if (ok[k] && stamp[k] !== i) { stamp[k] = i; c++; }
    }
    vol[i] = c;
  }
  return { deg, vol };
}

function mainStats(eOn: Uint8Array, nOn: Uint8Array, ok: Uint8Array): MainStats {
  let nodes = 0, edges = 0;
  for (let i = 0; i < N.length; i++) if (!N[i]!.extended) nodes += nOn[i]!;
  const dimActivities = [0, 0, 0, 0, 0];
  const seen = new Uint8Array(NCODES);
  for (let j = 0; j < E.length; j++) {
    if (!eOn[j]) continue;
    edges++;
    E[j]!.cd.forEach((arr, d) => { for (const k of arr) if (ok[k] && !seen[k]) { seen[k] = 1; dimActivities[d]!++; } });
  }
  const totalActivities = dimActivities.reduce((s, x) => s + x, 0);
  return { nodes, edges, avgDegree: nodes ? (2 * edges) / nodes : 0, dimActivities, totalActivities };
}

let memo: View | null = null;
/** Recorte atual (recalculado só quando os filtros ou a rede ampliada mudam). */
export function getView(): View {
  const ver = filterVer();
  if (memo && memo.ver === ver) return memo;
  const { inWin, ok } = activityMasks();
  const { fsum, eOn, facets } = filterEdges(inWin, ok);
  const nOn = filterNodes(eOn);
  memo = { ver, inWin, ok, fsum, eOn, nOn, ...nodeTotals(eOn, nOn, ok), facets, stats: mainStats(eOn, nOn, ok) };
  return memo;
}

/** Atividades distintas de um nó, por dimensão, dentro do recorte. */
export function nodeDims(i: number, v: View = getView()): number[] {
  const out = [0, 0, 0, 0, 0];
  const seen = new Set<number>();
  for (const j of N[i]!.adj) {
    if (!v.eOn[j]) continue;
    E[j]!.cd.forEach((arr, d) => { for (const k of arr) if (v.ok[k] && !seen.has(k)) { seen.add(k); out[d]!++; } });
  }
  return out;
}
