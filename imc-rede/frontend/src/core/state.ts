// Estado centralizado da interface + barramento de eventos.
//
// Tópicos:
//  - 'filters'   qualquer filtro mudou → invalida os seletores memoizados (core/selectors.ts)
//  - 'selection' nó/aresta selecionado mudou (e, com o modo ego ligado, o recorte também)
//  - 'view'      só a aparência mudou (hover, câmera, cores, tamanho) → redesenha o canvas
import type { GNode, UIState } from '../types/graph';
import { E, N, YMAX, YMIN } from './model';

export const S: UIState = {
  W: 0, H: 0, dpr: window.devicePixelRatio || 1, k: 0.3, tx: 0, ty: 0, sel: -1, selE: -1, hov: -1,
  minS: 1, showLab: true, showExt: true, colorMode: 'inst', layoutMode: 'free',
  sizeMetric: 'deg', y0: 0, y1: 0, ego: false, physics: true,
};
export const typeOn: Record<string, boolean> = {};
export const grpOn: Record<string, boolean> = { 'Computação': true, 'Matemática': true, 'Outras': true };
/** Dimensões ativas: art, prj, ori, ban, ptt. */
export const dimOn: boolean[] = [true, true, true, true, true];

/** Pesquisador do IMC passa no filtro de área? (nós de outros institutos sempre passam). */
export const imcVis = (n: GNode): boolean =>
  n.inst !== 'IMC' || (n.comp && !!grpOn['Computação']) || (n.mat && !!grpOn['Matemática']) ||
  (!n.comp && !n.mat && !!grpOn['Outras']);

export const yearFull = (): boolean => S.y0 <= YMIN && S.y1 >= YMAX;

// ---- Barramento ----
type Topic = 'filters' | 'selection' | 'view';
const subs: Record<Topic, (() => void)[]> = { filters: [], selection: [], view: [] };
let ver = 0;
/** Versão dos filtros: muda a cada emit('filters'); é a chave da memoização. */
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
  // Tipos de relação em ordem decrescente de frequência (ordem fixa da lista na sidebar).
  const cnt: Record<string, number> = {};
  E.forEach((e) => { cnt[e.tipo] = (cnt[e.tipo] ?? 0) + 1; });
  Object.keys(cnt).sort((a, b) => cnt[b]! - cnt[a]! || a.localeCompare(b)).forEach((t) => { typeOn[t] = true; });
  S.y0 = YMIN; S.y1 = YMAX;
}

/** Volta todos os filtros ao estado inicial (tudo visível). */
export function resetFilters(): void {
  Object.keys(typeOn).forEach((t) => { typeOn[t] = true; });
  Object.keys(grpOn).forEach((g) => { grpOn[g] = true; });
  dimOn.fill(true);
  S.y0 = YMIN; S.y1 = YMAX; S.minS = 1; S.showExt = true; S.ego = false;
  emit('filters');
}

/** Quantos pesquisadores existem no total (denominador do HUD). */
export const totalNodes = (): number => N.length;
