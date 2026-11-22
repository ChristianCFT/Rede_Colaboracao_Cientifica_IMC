// painel da direita
import { $ } from '../../core/dom';
import { display, on, selection } from '../../core/state';
import { pickEdge, pickNode } from '../../graph/interaction/selection';
import { edgeView } from './edgeView';
import { bindNodeView, nodeView } from './nodeView';
import { edgePesoView, nodePesoView, summaryPesoView } from './pesoView';
import { summaryView } from './summaryView';

function conteudo(render: () => void): string {
  if (display.peso) {
    return selection.node >= 0 ? nodePesoView(selection.node)
      : selection.edge >= 0 ? edgePesoView(selection.edge) : summaryPesoView();
  }
  return selection.node >= 0 ? nodeView(selection.node, render)
    : selection.edge >= 0 ? edgeView(selection.edge) : summaryView();
}

export function initDetails(): void {
  const side = $('side');
  let lastSel = -2, lastE = -2;
  const render = (): void => {
    const changed = selection.node !== lastSel || selection.edge !== lastE;
    lastSel = selection.node; lastE = selection.edge;
    const keep = side.scrollTop;
    side.innerHTML = conteudo(render);
    side.scrollTop = changed ? 0 : keep;
    side.querySelectorAll<HTMLElement>('[data-e]').forEach((d) => {
      d.addEventListener('click', (ev) => { ev.preventDefault(); ev.stopPropagation(); pickEdge(Number(d.dataset['e'])); });
    });
    side.querySelectorAll<HTMLElement>('[data-n]').forEach((d) => {
      d.addEventListener('click', (ev) => { ev.preventDefault(); pickNode(Number(d.dataset['n']), true); });
    });
    // Enter/Espaço também funcionam
    side.querySelectorAll<HTMLElement>('div[data-n], div[data-e], span[data-e]').forEach((d) => {
      d.tabIndex = 0; d.setAttribute('role', 'button');
      d.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); d.click(); } });
    });
    if (selection.node >= 0) bindNodeView(side);
  };
  on('filters', render); on('selection', render); on('peso', render);
  render();
}
