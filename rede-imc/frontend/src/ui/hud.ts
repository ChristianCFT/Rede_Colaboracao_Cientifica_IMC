// HUD: indicadores sempre da rede principal
import { $, fmt, fmt1, pct } from '../core/dom';
import { DIMN, MAIN_EDGES, MAIN_NODES, dimCol } from '../core/model';
import { on } from '../core/state';
import { getView } from '../core/selectors';

const kpi = (label: string, value: string): string =>
  `<div class="kpi"><span class="kl">${label}</span><span class="kv">${value}</span></div>`;

export function initHUD(): void {
  const el = $('hud');
  let last = '';
  const paint = (): void => {
    const s = getView().stats;
    let top = -1;
    s.dimActivities.forEach((c, j) => { if (c > 0 && (top < 0 || c > s.dimActivities[top]!)) top = j; });
    const dom = top < 0 ? '<span class="of">—</span>'
      : `<span class="sw" style="background:${dimCol(top)}"></span><b>${DIMN[top] ?? ''}</b><span class="of">•</span>${pct(s.dimActivities[top]! / s.totalActivities)}`;
    const html =
      kpi('Pesquisadores visíveis', `<b>${fmt(s.nodes)}</b><span class="of">/ ${fmt(MAIN_NODES)}</span>`) +
      kpi('Conexões ativas', `<b>${fmt(s.edges)}</b><span class="of">/ ${fmt(MAIN_EDGES)}</span>`) +
      kpi('Dimensão predominante', dom) +
      kpi('Grau médio', `<b>${fmt1(s.avgDegree)}</b><span class="of">parceiros/nó</span>`);
    if (html !== last) { el.innerHTML = html; last = html; }
  };
  on('filters', paint);
  paint();
}
