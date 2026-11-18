// Seção "Exibição da rede": inclui ou retira os pesquisadores sem colaboração com o IMC.
// São só vértices, em anel ao redor da rede principal (posições vindas do backend), então ligar e
// desligar não move a rede principal; a câmera apenas reenquadra o que ficou visível.
import { $, fmt } from '../../core/dom';
import { EXTENDED_NODES, N } from '../../core/model';
import { emit, extended, selection } from '../../core/state';
import { fitView } from '../../graph/interaction/camera';
import { clearSelection } from '../../graph/interaction/selection';

export function initNetwork(): void {
  const box = $<HTMLInputElement>('extended');
  $('extendedCount').textContent = fmt(EXTENDED_NODES);
  box.closest('label')?.classList.toggle('zero', EXTENDED_NODES === 0);
  box.addEventListener('change', () => {
    extended.visible = box.checked;
    emit('filters');
    if (!extended.visible && selection.node >= 0 && N[selection.node]!.extended) clearSelection();
    fitView();
  });
}
