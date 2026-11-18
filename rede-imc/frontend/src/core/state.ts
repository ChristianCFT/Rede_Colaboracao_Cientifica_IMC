// Estado da interface, separado por responsabilidade, + barramento de eventos.
//
// Tópicos:
//  - 'filters'   o recorte mudou (filtros ou rede ampliada) → invalida o recorte memoizado (selectors.ts)
//  - 'selection' nó/aresta selecionado mudou
//  - 'view'      só a aparência mudou (hover, câmera, cores, rótulos) → redesenha o canvas
import type { ColorMode, GNode, LayoutMode } from './types';
import { E, YMAX, YMIN } from './model';

/** Câmera: tamanho da área do canvas e transformação mundo → tela (x·k + tx). */
export const camera = { W: 0, H: 0, dpr: window.devicePixelRatio || 1, k: 0.3, tx: 0, ty: 0 };

/** Seleção e hover: índices em N / E (-1 = nenhum). */
export const selection = { node: -1, edge: -1, hover: -1 };

/** Filtros do recorte da rede. */
export const filters = {
  /** Dimensões ativas: art, prj, ori, ban, ptt. */
  dims: [true, true, true, true, true],
  /** Tipos de relação da rede principal (IMC-IMC, IMC-EXT...). */
  types: {} as Record<string, boolean>,
  /** Áreas do IMC. */
  groups: { 'Computação': true, 'Matemática': true, 'Outras': true } as Record<string, boolean>,
  yearFrom: 0,
  yearTo: 0,
  minActivities: 1,
  showExternal: true,
};

/** Controles de exibição: não alteram o recorte, só o desenho. */
export const display = {
  colorMode: 'inst' as ColorMode,
  layoutMode: 'free' as LayoutMode,
  labelsImc: true,
  physics: true,
};

/** Pesquisadores sem colaboração com o IMC (só vértices, em anel ao redor da rede principal). */
export const extended = { visible: false };

/** Pesquisador do IMC passa no filtro de área? (pesquisadores de fora do IMC sempre passam). */
export const passesArea = (n: GNode): boolean =>
  n.inst !== 'IMC' || (n.comp && !!filters.groups['Computação']) || (n.mat && !!filters.groups['Matemática']) ||
  (!n.comp && !n.mat && !!filters.groups['Outras']);

/** A janela temporal cobre todo o período? (atividades sem ano só contam nesse caso). */
export const fullYearRange = (): boolean => filters.yearFrom <= YMIN && filters.yearTo >= YMAX;

// ---- Barramento ----
type Topic = 'filters' | 'selection' | 'view';
const subs: Record<Topic, (() => void)[]> = { filters: [], selection: [], view: [] };
let ver = 0;
/** Versão do recorte: muda a cada emit('filters'); é a chave da memoização. */
export const filterVer = (): number => ver;
export const on = (t: Topic, fn: () => void): void => { subs[t].push(fn); };
export function emit(t: Topic): void {
  if (t === 'filters') ver++;
  subs[t].forEach((f) => f());
}

/** Agrupa emissões disparadas na mesma tarefa (usado pelos sliders durante o arraste). */
const pendingTopics = new Set<Topic>();
let soon = false;
export function emitSoon(t: Topic): void {
  pendingTopics.add(t);
  if (soon) return;
  soon = true;
  queueMicrotask(() => { soon = false; const ts = [...pendingTopics]; pendingTopics.clear(); ts.forEach(emit); });
}

export function initState(): void {
  // Tipos de relação da rede principal em ordem decrescente de frequência (ordem fixa da lista na sidebar).
  const cnt: Record<string, number> = {};
  E.forEach((e) => { cnt[e.tipo] = (cnt[e.tipo] ?? 0) + 1; });
  Object.keys(cnt).sort((a, b) => cnt[b]! - cnt[a]! || a.localeCompare(b)).forEach((t) => { filters.types[t] = true; });
  filters.yearFrom = YMIN; filters.yearTo = YMAX;
}

/** Volta todos os filtros ao estado inicial (tudo visível). */
export function resetFilters(): void {
  Object.keys(filters.types).forEach((t) => { filters.types[t] = true; });
  Object.keys(filters.groups).forEach((g) => { filters.groups[g] = true; });
  filters.dims.fill(true);
  filters.yearFrom = YMIN; filters.yearTo = YMAX; filters.minActivities = 1; filters.showExternal = true;
  emit('filters');
}
