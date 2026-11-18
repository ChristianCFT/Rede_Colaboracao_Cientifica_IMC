// HUD de KPIs no topo do canvas, recalculado a cada mudança de recorte (valores memoizados).
import { $, fmt, fmt1, pct } from '../core/dom';
import { DIMN, DIM_LONG, E, N, dimCol } from '../core/model';
import { on } from '../core/state';
import { getView } from '../core/selectors';

const kpi = (label: string, value: string, title = ''): string =>
  `<div class="kpi"${title ? ` title="${title}"` : ''}><span class="kl">${label}</span><span class="kv">${value}</span></div>`;

export function initHUD(): void {
  const el = $('hud');
  let last = '';
  const paint = (): void => {
    const v = getView();
    let top = -1;
    v.dimAct.forEach((c, j) => { if (c > 0 && (top < 0 || c > v.dimAct[top]!)) top = j; });
    const dom = top < 0 ? '<span class="of">—</span>'
      : `<span class="sw" style="background:${dimCol(top)}"></span><b>${DIMN[top] ?? ''}</b><span class="of">•</span>${pct(v.dimAct[top]! / v.totAct)}`;
    const html =
      kpi('Pesquisadores visíveis', `<b>${fmt(v.nN)}</b><span class="of">/ ${fmt(N.length)}</span>`) +
      kpi('Conexões ativas', `<b>${fmt(v.nE)}</b><span class="of">/ ${fmt(E.length)}</span>`) +
      kpi('Dimensão predominante', dom, top < 0 ? '' : `${DIM_LONG[top]}: ${fmt(v.dimAct[top]!)} de ${fmt(v.totAct)} atividades distintas no recorte`) +
      kpi('Grau médio', `<b>${fmt1(v.avgDeg)}</b><span class="of">parceiros/nó</span>`);
    if (html !== last) { el.innerHTML = html; last = html; }
  };
  on('filters', paint); on('selection', paint);
  paint();
}
