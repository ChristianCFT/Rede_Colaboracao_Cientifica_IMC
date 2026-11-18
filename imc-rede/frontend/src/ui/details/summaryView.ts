// Estado vazio do painel: resumo executivo do recorte atual.
import { esc, fmt } from '../../core/dom';
import { N, col } from '../../core/model';
import { getView } from '../../core/selectors';
import { bars, personRow } from './parts';

export function summaryView(): string {
  const v = getView();
  const vis: number[] = [];
  for (let i = 0; i < N.length; i++) if (v.nOn[i]) vis.push(i);
  const top = [...vis].sort((a, b) => v.deg[b]! - v.deg[a]! || v.vol[b]! - v.vol[a]!).slice(0, 5).filter((i) => v.deg[i]! > 0);
  const byInst = new Map<string, number>();
  vis.forEach((i) => { const s = N[i]!.inst; byInst.set(s, (byInst.get(s) ?? 0) + 1); });
  const inst = [...byInst.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

  return `<h1>Resumo do recorte atual</h1>
  <h2>Mais conectados no recorte</h2>
  <div class="li">${top.length ? top.map((i, k) => personRow(k + 1, i, `<span class="cnt">${fmt(v.deg[i]!)}</span>`)).join('') : '<span class="mu">Nenhuma conexão com os filtros atuais.</span>'}</div>
  <h2>Pesquisadores por instituto</h2>
  ${inst.length ? bars(inst.map(([s, c]) => ({ label: s, color: col(s), value: c, frac: c / v.nN }))) : '<span class="mu">Nenhum pesquisador visível.</span>'}
  <p class="mu empty">${esc('Clique em um pesquisador ou em uma aresta para ver os detalhes.')}</p>`;
}
