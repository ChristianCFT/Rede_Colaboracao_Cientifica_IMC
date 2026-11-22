// painel da direita no modo peso
import { esc, fmt, fmtPeso } from '../../core/dom';
import { DIM_LONG, E, N, col, dimCol } from '../../core/model';
import { ALFA, REF } from '../../core/peso';
import { getView } from '../../core/selectors';
import type { View } from '../../core/selectors';
import { allOpen, cabecalho } from './nodeView';
import { dot, nameLink, personRow } from './parts';
import { origem, porInstituto, visiveis } from './summaryView';

/** empates dividem a posição */
function posicao(valor: number, valores: number[]): number {
  let maiores = 0;
  for (const x of valores) if (x > valor) maiores++;
  return maiores + 1;
}

function pesosVisiveis(v: View): number[] {
  const out: number[] = [];
  for (let j = 0; j < E.length; j++) if (v.eOn[j]) out.push(v.fw[j]!);
  return out;
}

/** explicação da fórmula */
function comoCalcula(): string {
  const tipos = [0, 1, 2, 4, 3]; // maior pra menor importância
  const linhas = tipos.map((j) =>
    `<span>${dot(dimCol(j))}${esc(DIM_LONG[j] ?? '')}</span><b class="num">${Math.round((ALFA[j] ?? 0) * 100)}%</b><span class="mu num">${fmt(REF[j] ?? 0)}</span>`).join('');
  return `<details class="como"><summary>Como o peso é calculado</summary>
  <p>Para cada tipo de atividade, as atividades em comum da dupla passam por ln(1 + x), para que as primeiras
  contem mais que as seguintes, e são divididas pelo maior valor da rede naquele tipo. Cada tipo fica entre 0 e 1.</p>
  <p>O peso é a soma desses valores, cada um multiplicado pela importância do tipo:</p>
  <div class="alfas"><span class="mu">Tipo</span><span class="mu">Importância</span><span class="mu">Maior na rede</span>${linhas}</div>
  <p class="mu sm">0 = nenhuma atividade em comum no recorte. 1 = o maior valor da rede em todos os tipos.
  A espessura da aresta no grafo acompanha o peso.</p></details>`;
}

export function edgePesoView(i: number): string {
  const e = E[i]!, v = getView(), w = v.fw[i]!;
  let lugar = '<span class="mu">Fora do recorte atual.</span>';
  if (v.eOn[i]) {
    const pesos = pesosVisiveis(v);
    lugar = `${fmt(posicao(w, pesos))}ª relação mais forte de ${fmt(pesos.length)} no recorte`;
  }
  // só se o recorte deixou alguma atividade de fora
  const parcial = v.fsum[i] !== e.sum
    ? `<p class="mu sm">Com todas as atividades da dupla, o peso é <b>${fmtPeso(e.w)}</b>. Os filtros de dimensão e de período deixam de fora parte delas.</p>`
    : '';
  return `<h1>${nameLink(e.a)} ↔ ${nameLink(e.b)}</h1><span class="mu">${esc(e.tipo)}</span>
  <h2>Peso da colaboração</h2>
  <div class="peso"><b class="num">${fmtPeso(w)}</b></div>
  <div class="escala"><span style="width:${(Math.min(1, w) * 100).toFixed(1)}%"></span></div>
  <div class="ends mu num"><span>0</span><span>1</span></div>
  <div class="mu meta">${lugar}</div>${parcial}${comoCalcula()}`;
}

export function nodePesoView(i: number): string {
  const v = getView();
  const parceiros = N[i]!.adj.filter((j) => v.eOn[j])
    .map((j) => ({ e: j, o: E[j]!.a === i ? E[j]!.b : E[j]!.a, w: v.fw[j]! }))
    .sort((p, q) => q.w - p.w || N[p.o]!.name.localeCompare(N[q.o]!.name));
  const top = parceiros.slice(0, 5).map((p, k) =>
    personRow(k + 1, p.o, `<span class="go" data-e="${p.e}" title="Ver o peso da relação">${fmtPeso(p.w)} ›</span>`)).join('');
  const todas = parceiros.map((p) => {
    const o = N[p.o]!;
    return `<div data-e="${p.e}">${dot(col(o.inst))} ${esc(o.name)} <span class="mu">· ${esc(o.inst)} · <span class="num">${fmtPeso(p.w)}</span></span></div>`;
  }).join('');
  return `${cabecalho(i, v)}
  <h2>Top 5 parceiros por peso</h2>
  <div class="li">${top || '<span class="mu">Nenhum com os filtros atuais.</span>'}</div>
  <details class="all"${allOpen ? ' open' : ''}><summary>Todas as conexões (${fmt(parceiros.length)})</summary>
  <div class="li">${todas || '<span class="mu">Nenhuma com os filtros atuais.</span>'}</div></details>`;
}

export function summaryPesoView(): string {
  const v = getView();
  const relacoes: number[] = [];
  for (let j = 0; j < E.length; j++) if (v.eOn[j]) relacoes.push(j);
  relacoes.sort((p, q) => v.fw[q]! - v.fw[p]!);
  const topRelacoes = relacoes.slice(0, 5).map((j, k) =>
    `<div class="pr" data-e="${j}"><span class="rk">${k + 1}</span><span class="nm">${esc(N[E[j]!.a]!.name)} ↔ ${esc(N[E[j]!.b]!.name)}</span><span class="cnt num">${fmtPeso(v.fw[j]!)}</span></div>`).join('');

  return `<h1>Resumo do recorte atual</h1>${origem()}
  <h2>Relações mais fortes</h2>
  <div class="li">${topRelacoes || '<span class="mu">Nenhuma relação com os filtros atuais.</span>'}</div>
  ${porInstituto(v, visiveis(v))}
  <p class="mu empty">Clique em um pesquisador ou em uma aresta para ver os detalhes.</p>`;
}
