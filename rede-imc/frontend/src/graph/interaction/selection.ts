// Ações de seleção compartilhadas por canvas, busca e painel de detalhes.
import { selection, emit } from '../../core/state';
import { centerOn } from './camera';

export function pickNode(i: number, center = false): void {
  selection.node = i; selection.edge = -1;
  emit('selection');
  if (center) centerOn(i);
}

export function pickEdge(i: number): void {
  selection.edge = i; selection.node = -1;
  emit('selection');
}

export function clearSelection(): void {
  selection.node = -1; selection.edge = -1;
  emit('selection');
}
