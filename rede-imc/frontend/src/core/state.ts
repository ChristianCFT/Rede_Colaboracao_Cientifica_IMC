// estado da interface + eventos (filters, selection, view, peso)
import type { ColorMode, GNode, LayoutMode } from './types';
import { E, YMAX, YMIN } from './model';

/** mundo → tela: x·k + tx */
export const camera = { W: 0, H: 0, dpr: window.devicePixelRatio || 1, k: 0.3, tx: 0, ty: 0 };

/** -1 = nenhum */
export const selection = { node: -1, edge: -1, hover: -1 };

export const filters = {
  dims: [true, true, true, true, true],
  /** IMC-IMC, IMC-EXT... */
  types: {} as Record<string, boolean>,
  groups: { 'Computação': true, 'Matemática': true, 'Outras': true } as Record<string, boolean>,
  yearFrom: 0,
  yearTo: 0,
  minActivities: 1,
  showExternal: true,
};

/** só mudam o desenho */
export const display = {
  colorMode: 'inst' as ColorMode,
  layoutMode: 'free' as LayoutMode,
  labelsImc: true,
  physics: true,
  /** desligado usa a contagem de atividades */
  peso: false,
};

export function setPeso(ligado: boolean): void {
  display.peso = ligado;
  emit('peso');
}

export const extended = { visible: false };

/** quem não é do IMC sempre passa */
export const passesArea = (n: GNode): boolean =>
  n.inst !== 'IMC' || (n.comp && !!filters.groups['Computação']) || (n.mat && !!filters.groups['Matemática']) ||
  (!n.comp && !n.mat && !!filters.groups['Outras']);

/** atividades sem ano só contam se a janela pega tudo */
export const fullYearRange = (): boolean => filters.yearFrom <= YMIN && filters.yearTo >= YMAX;

// eventos
type Topic = 'filters' | 'selection' | 'view' | 'peso';
const subs: Record<Topic, (() => void)[]> = { filters: [], selection: [], view: [], peso: [] };
let ver = 0;
/** chave da memoização */
export const filterVer = (): number => ver;
export const on = (t: Topic, fn: () => void): void => { subs[t].push(fn); };
export function emit(t: Topic): void {
  if (t === 'filters') ver++;
  subs[t].forEach((f) => f());
}

/** usado pelos sliders durante o arraste */
const pendingTopics = new Set<Topic>();
let soon = false;
export function emitSoon(t: Topic): void {
  pendingTopics.add(t);
  if (soon) return;
  soon = true;
  queueMicrotask(() => { soon = false; const ts = [...pendingTopics]; pendingTopics.clear(); ts.forEach(emit); });
}

export function initState(): void {
  // ordem decrescente de frequência
  const cnt: Record<string, number> = {};
  E.forEach((e) => { cnt[e.tipo] = (cnt[e.tipo] ?? 0) + 1; });
  Object.keys(cnt).sort((a, b) => cnt[b]! - cnt[a]! || a.localeCompare(b)).forEach((t) => { filters.types[t] = true; });
  filters.yearFrom = YMIN; filters.yearTo = YMAX;
}

export function resetFilters(): void {
  Object.keys(filters.types).forEach((t) => { filters.types[t] = true; });
  Object.keys(filters.groups).forEach((g) => { filters.groups[g] = true; });
  filters.dims.fill(true);
  filters.yearFrom = YMIN; filters.yearTo = YMAX; filters.minActivities = 1; filters.showExternal = true;
  emit('filters');
}
