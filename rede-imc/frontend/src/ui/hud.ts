// HUD de KPIs no topo do canvas. Os indicadores representam sempre a rede principal do IMC; com a
// pesquisadores sem colaboração visíveis, a dica (title) das contagens deixa isso explícito.
import { $, fmt, fmt1, pct } from '../core/dom';
import { DIMN, DIM_LONG, EXTENDED_NODES, MAIN_EDGES, MAIN_NODES, dimCol } from '../core/model';
import { extended, on } from '../core/state';
import { getView } from '../core/selectors';

const kpi = (label: string, value: string, title = ''): string =>
  `<div class="kpi"${title ? ` title="${title}"` : ''}><span class="kl">${label}</span><span class="kv">${value}</span></div>`;

export function initHUD(): void {
  const el = $('hud');
  let last = '';
  const paint = (): void => {
    const s = getView().stats;
    let top = -1;
    s.dimActivities.forEach((c, j) => { if (c > 0 && (top < 0 || c > s.dimActivities[top]!)) top = j; });
    const dom = top < 0 ? '<span class="of">—</span>'
      : `<span class="sw" style="background:${dimCol(top)}"></span><b>${DIMN[top] ?? ''}</b><span class="of">•</span>${pct(s.dimActivities[top]! / s.totalActivities)}`;
    const origin = extended.visible
      ? `Rede principal do IMC (não inclui os ${fmt(EXTENDED_NODES)} pesquisadores sem colaboração com o IMC)` : '';
    const html =
      kpi('Pesquisadores visíveis', `<b>${fmt(s.nodes)}</b><span class="of">/ ${fmt(MAIN_NODES)}</span>`, origin) +
      kpi('Conexões ativas', `<b>${fmt(s.edges)}</b><span class="of">/ ${fmt(MAIN_EDGES)}</span>`, origin) +
      kpi('Dimensão predominante', dom, top < 0 ? '' : `${DIM_LONG[top]}: ${fmt(s.dimActivities[top]!)} de ${fmt(s.totalActivities)} atividades distintas no recorte`) +
      kpi('Grau médio', `<b>${fmt1(s.avgDegree)}</b><span class="of">parceiros/nó</span>`);
    if (html !== last) { el.innerHTML = html; last = html; }
  };
  on('filters', paint);
  paint();
}
