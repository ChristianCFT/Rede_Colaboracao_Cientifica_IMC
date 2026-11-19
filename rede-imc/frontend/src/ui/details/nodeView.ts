// Painel de um pesquisador: identificação, barras das 5 dimensões, Top 5 parceiros e conexões.
// Vale para os dois universos; quem não colabora com o IMC aparece sem barras nem parceiros.
import { esc, fmt } from '../../core/dom';
import { DIMN, DIM_LONG, E, GC, IX, N, col, dimCol } from '../../core/model';
import { filters } from '../../core/state';
import { getView, nodeDims } from '../../core/selectors';
import type { View } from '../../core/selectors';
import { api } from '../../api/api';
import type { NodeDetailDTO } from '../../api/api';
import { bars, dot, personRow } from './parts';

// Detalhe vindo de GET /nodes/{id}: define a ordem da lista completa de conexões.
const detail = new Map<string, NodeDetailDTO>();
const loading = new Set<string>();
/** "Todas as conexões" aberta ou fechada (vale também para o painel do modo peso). */
export let allOpen = false;

/** Identificação do pesquisador: nome, instituto, área, parceiros, Lattes e avisos (os dois modos usam). */
export function cabecalho(i: number, v: View): string {
  const n = N[i]!;
  const out = !v.nOn[i] ? '<p class="mu">Fora do recorte atual — ajuste os filtros para vê-lo no grafo.</p>' : '';
  const noImc = n.extended ? '<p class="mu">Sem colaboração direta registrada com pesquisadores do IMC.</p>' : '';
  const degTxt = v.deg[i] === n.deg ? `${fmt(n.deg)} parceiros` : `${fmt(v.deg[i]!)} de ${fmt(n.deg)} parceiros no recorte`;
  return `<h1>${esc(n.name)}</h1><span class="badge" style="background:${col(n.inst)}">${esc(n.inst)}</span> ${n.inst === 'IMC' ? `<span class="badge" style="background:${GC[n.grp] ?? '#444'}">${esc(n.grp)}</span> ` : ''}<span class="mu num">${degTxt}</span>
  <p>${n.area ? esc(n.area) : '<span class="mu">Área de atuação ausente na fonte</span>'}</p>${n.lat ? `<p><a href="${esc(n.lat)}" target="_blank" rel="noopener">Currículo Lattes</a></p>` : ''}${noImc}${out}`;
}

export function nodeView(i: number, rerender: () => void): string {
  const n = N[i]!, v = getView(), fs = v.fsum;
  const partners = n.adj.filter((j) => v.eOn[j]).map((j) => ({ e: j, o: E[j]!.a === i ? E[j]!.b : E[j]!.a, w: fs[j]! }))
    .sort((p, q) => q.w - p.w || N[p.o]!.name.localeCompare(N[q.o]!.name));
  const dims = nodeDims(i, v), tot = dims.reduce((s, x) => s + x, 0);

  // Lista completa: ordem da API quando disponível, senão local; contagens sempre do recorte.
  const d = detail.get(n.id);
  let order = partners;
  if (d) {
    const rank = new Map(d.vizinhos.map((x, k) => [IX.get(x.id) ?? -1, k]));
    order = [...partners].sort((p, q) => (rank.get(p.o) ?? 1e9) - (rank.get(q.o) ?? 1e9));
  } else if (!loading.has(n.id)) {
    loading.add(n.id);
    api.node(n.id).then((x) => { detail.set(n.id, x); rerender(); }).catch(() => undefined).finally(() => loading.delete(n.id));
  }
  const all = order.map((p) => {
    const o = N[p.o]!;
    return `<div data-e="${p.e}">${dot(col(o.inst))} ${esc(o.name)} <span class="mu">· ${esc(o.inst)} · <span class="num">${fmt(p.w)}</span></span></div>`;
  }).join('');

  return `${cabecalho(i, v)}
  <h2>Colaborações por dimensão</h2>
  ${tot ? bars(dims.map((c, j) => ({ label: DIMN[j] ?? '', title: DIM_LONG[j], color: dimCol(j), value: c, frac: c / tot, muted: !filters.dims[j] })))
    : '<p class="mu">Nenhuma colaboração no recorte atual.</p>'}
  <div class="mu sm">Atividades distintas com parceiros visíveis no recorte (${fmt(tot)}).</div>
  <h2>Top 5 parceiros</h2>
  <div class="li">${partners.length ? partners.slice(0, 5).map((p, k) =>
    personRow(k + 1, p.o, `<span class="go" data-e="${p.e}" title="Ver colaborações em comum">${fmt(p.w)} ›</span>`)).join('')
    : '<span class="mu">Nenhum com os filtros atuais.</span>'}</div>
  <details class="all"${allOpen ? ' open' : ''}><summary>Todas as conexões (${fmt(partners.length)})</summary>
  <div class="li">${all || '<span class="mu">Nenhuma com os filtros atuais.</span>'}</div></details>`;
}

export function bindNodeView(root: HTMLElement): void {
  root.querySelector<HTMLDetailsElement>('details.all')?.addEventListener('toggle', (e) => { allOpen = (e.target as HTMLDetailsElement).open; });
}
