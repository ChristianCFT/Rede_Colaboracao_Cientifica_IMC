// Modelo de domínio no cliente: nós, arestas, adjacência, atividades e helpers.
import type { GEdge, GNode, GraphDTO, Pt } from '../types/graph';

export { $, esc } from './dom';

export let N: GNode[] = [];
export let E: GEdge[] = [];
export let A: Record<string, [string, string]> = {};
export let PAL: Record<string, string> = {};
export let GC: Record<string, string> = {};
/** Nomes curtos das 5 dimensões, vindos da API (ex.: "Artigos"). */
export let DIMN: string[] = [];
export let IX = new Map<string, number>();
export const col = (inst: string): string => PAL[inst] ?? '#444';

/** Nomes por extenso usados nos filtros e no painel (mesma ordem de DIMN: art, prj, ori, ban, ptt). */
export const DIM_LONG = ['Artigos científicos', 'Projetos de pesquisa', 'Orientações', 'Bancas', 'Produção técnico-tecnológica'];
/** Cor de cada dimensão: variável CSS (troca sozinha entre tema claro e escuro). */
export const dimCol = (j: number): string => `var(--d${j})`;

// ---- Índice inteiro das atividades (acelera filtros por dimensão e por ano) ----
export let NCODES = 0;
/** Código textual de cada atividade (ex.: "ART-000123"). */
export let CODE: string[] = [];
/** Dimensão (0..4) de cada atividade. */
export let CODE_DIM = new Uint8Array(0);
/** Ano de cada atividade; 0 quando ausente ou inválido. */
export let CODE_YEAR = new Int16Array(0);
/** Faixa de anos válidos presente nos dados. */
export let YMIN = 0;
export let YMAX = 0;
/** Atividades sem ano válido (contam apenas quando a janela temporal cobre todo o período). */
export let NO_YEAR = 0;
/** Maior grau da rede completa: referência de escala do tamanho dos nós. */
export let MAX_DEG = 1;

const parseYear = (s: string | undefined): number => {
  const y = Number.parseInt(String(s ?? '').slice(0, 4), 10);
  const lim = new Date().getFullYear() + 1;
  return Number.isFinite(y) && y >= 1900 && y <= lim ? y : 0;
};

export function initModel(g: GraphDTO): void {
  PAL = g.paleta; GC = g.cores_grupo; DIMN = g.dimensoes;
  A = Object.fromEntries(Object.entries(g.atividades).map(([id, a]) => [id, [a.ano, a.titulo] as [string, string]]));
  const ix = new Map(g.nodes.map((n, i) => [n.id, i]));
  IX = ix;
  N = g.nodes.map((n, i) => ({
    i, id: n.id, name: n.label, inst: n.instituto, area: n.area, deg: n.grau, x: n.x, y: n.y, lat: n.lattes_url,
    prod: n.producao ? [n.producao.art, n.producao.prj, n.producao.ori, n.producao.ban, n.producao.ptt] : null,
    obs: n.observacao, grp: n.grupo, comp: n.comp, mat: n.mat, cen: n.centralidade_grau, btw: n.intermediacao,
    lay: { free: [n.x, n.y] as Pt, area: [n.x_area, n.y_area] as Pt }, adj: [], ax: n.x, ay: n.y,
  }));

  // Códigos de atividade → inteiros (dimensão e ano por índice).
  const codeIx = new Map<string, number>();
  const dims: number[] = [], years: number[] = [];
  CODE = [];
  const codeOf = (c: string, j: number): number => {
    let k = codeIx.get(c);
    if (k === undefined) {
      k = CODE.length; codeIx.set(c, k); CODE.push(c); dims.push(j); years.push(parseYear(A[c]?.[0]));
    }
    return k;
  };
  E = g.edges.flatMap((e) => {
    const a = ix.get(e.source), b = ix.get(e.target);
    if (a === undefined || b === undefined) return [];
    const cd = e.vetor_bruto.map((ids, j) => ids.map((c) => codeOf(c, j)));
    return [{ i: 0, a, b, tipo: e.tipo_relacao, vc: e.vetor_contagem, vb: e.vetor_bruto, sum: e.soma_bruta, cd }];
  }).map((e, i) => ({ ...e, i }));
  E.forEach((e) => { N[e.a]!.adj.push(e.i); N[e.b]!.adj.push(e.i); });

  NCODES = CODE.length;
  CODE_DIM = Uint8Array.from(dims);
  CODE_YEAR = Int16Array.from(years);
  const valid = years.filter((y) => y > 0);
  YMIN = valid.length ? Math.min(...valid) : 2000;
  YMAX = valid.length ? Math.max(...valid) : 2000;
  NO_YEAR = years.length - valid.length;
  MAX_DEG = Math.max(1, ...N.map((n) => n.deg));
}
