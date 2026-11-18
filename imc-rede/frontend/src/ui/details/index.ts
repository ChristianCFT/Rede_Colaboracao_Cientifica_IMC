// Painel direito (detalhes contextuais): resumo do recorte, pesquisador ou aresta.
import { $ } from '../../core/dom';
import { S, on } from '../../core/state';
import { pickEdge, pickNode } from '../../core/actions';
import { edgeView } from './edgeView';
import { bindNodeView, nodeView } from './nodeView';
import { summaryView } from './summaryView';

export function initDetails(): void {
  const side = $('side');
  let lastSel = -2, lastE = -2;
  const render = (): void => {
    const changed = S.sel !== lastSel || S.selE !== lastE;
    lastSel = S.sel; lastE = S.selE;
    const keep = side.scrollTop;
    side.innerHTML = S.sel >= 0 ? nodeView(S.sel, render) : S.selE >= 0 ? edgeView(S.selE) : summaryView();
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
    if (S.sel >= 0) bindNodeView(side);
  };
  on('filters', render); on('selection', render);
  render();
}
