// painel da aresta: colaborações por dimensão, mais recentes primeiro
import { esc, fmt } from '../../core/dom';
import { A, CODE, CODE_YEAR, DIM_LONG, E, dimCol } from '../../core/model';
import { getView } from '../../core/selectors';
import { dot, nameLink, vec } from './parts';

export function edgeView(i: number): string {
  const e = E[i]!, v = getView(), ok = v.ok;
  const inCut = v.fsum[i]!;
  let anyOut = false;
  const groups = e.cd.map((codes, j) => {
    if (!codes.length) return '';
    const items = codes.map((k) => {
      const code = CODE[k]!, a = A[code];
      return { code, ano: a?.[0] ?? '', tit: a?.[1] ?? '(não encontrada)', y: CODE_YEAR[k]!, ok: ok[k] === 1 };
    }).sort((p, q) => q.y - p.y || p.tit.localeCompare(q.tit));
    const nOk = items.filter((x) => x.ok).length;
    if (nOk < items.length) anyOut = true;
    return `<h2 class="grp-h">${dot(dimCol(j))}${esc(DIM_LONG[j] ?? '')}<span class="cnt num">${nOk < items.length ? `${fmt(nOk)} de ${fmt(items.length)}` : fmt(items.length)}</span></h2>` +
      items.map((x) => `<div class="act${x.ok ? '' : ' out'}"${x.ok ? '' : ' title="Fora do recorte atual"'}><span class="mu yr">${esc(x.ano || 's/ ano')}</span> ${esc(x.tit)} <span class="mu">· ${esc(x.code)}</span></div>`).join('');
  }).join('');
  return `<h1>${nameLink(e.a)} ↔ ${nameLink(e.b)}</h1><span class="mu">${esc(e.tipo)}</span>
  <div class="mu meta num">${fmt(e.sum)} colaborações em comum${inCut !== e.sum ? ` · ${fmt(inCut)} no recorte atual` : ''}</div>
  ${vec(e.vc)}${anyOut ? '<div class="mu sm">Itens esmaecidos estão fora do recorte atual.</div>' : ''}${groups}`;
}
