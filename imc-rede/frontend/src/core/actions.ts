// Ações de seleção compartilhadas por canvas, busca e painel (evita imports circulares).
// O modo ego depende do nó selecionado; por isso ele é desligado quando a seleção deixa de ser um nó.
import { S, emit } from './state';
import { centerOn, fitView } from '../canvas/camera';

export function pickNode(i: number, center = false): void {
  S.sel = i; S.selE = -1;
  emit('selection');
  if (S.ego) fitView();
  else if (center) centerOn(i);
}
export function pickEdge(i: number): void {
  S.selE = i; S.sel = -1; S.ego = false;
  emit('selection');
}
export function clearSelection(): void {
  S.sel = -1; S.selE = -1; S.ego = false;
  emit('selection');
}
export function setEgo(onOff: boolean): void {
  S.ego = onOff && S.sel >= 0;
  emit('selection');
  if (S.ego) fitView();
}
