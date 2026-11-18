// Painel direito (detalhes contextuais): resumo do recorte, pesquisador ou aresta.
import { $ } from '../../core/dom';
import { on, selection } from '../../core/state';
import { pickEdge, pickNode } from '../../graph/interaction/selection';
import { edgeView } from './edgeView';
import { bindNodeView, nodeView } from './nodeView';
import { summaryView } from './summaryView';

export function initDetails(): void {
  const side = $('side');
  let lastSel = -2, lastE = -2;
  const render = (): void => {
    const changed = selection.node !== lastSel || selection.edge !== lastE;
    lastSel = selection.node; lastE = selection.edge;
    const keep = side.scrollTop;
    side.innerHTML = selection.node >= 0 ? nodeView(selection.node, render)
      : selection.edge >= 0 ? edgeView(selection.edge) : summaryView();
    side.scrollTop = changed ? 0 : keep;
    side.querySelectorAll<HTMLElement>('[data-e]').forEach((d) => {
      d.addEventListener('click', (ev) => { ev.preventDefault(); ev.stopPropagation(); pickEdge(Number(d.dataset['e'])); });
    });
    side.querySelectorAll<HTMLElement>('[data-n]').forEach((d) => {
      d.addEventListener('click', (ev) => { ev.preventDefault(); pickNode(Number(d.dataset['n']), true); });
    });
    // Linhas clicáveis também respondem ao teclado (Tab + Enter/Espaço).
    side.querySelectorAll<HTMLElement>('div[data-n], div[data-e], span[data-e]').forEach((d) => {
      d.tabIndex = 0; d.setAttribute('role', 'button');
      d.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); d.click(); } });
    });
    if (selection.node >= 0) bindNodeView(side);
  };
  on('filters', render); on('selection', render);
  render();
}
