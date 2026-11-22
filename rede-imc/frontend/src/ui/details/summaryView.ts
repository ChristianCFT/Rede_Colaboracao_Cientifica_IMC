// resumo do recorte (painel vazio)
import { fmt } from '../../core/dom';
import { EXTENDED_NODES, N, col } from '../../core/model';
import { extended } from '../../core/state';
import { getView } from '../../core/selectors';
import type { View } from '../../core/selectors';
import { bars, personRow } from './parts';

/** só a rede principal */
export function visiveis(v: View): number[] {
  const vis: number[] = [];
  for (let i = 0; i < N.length; i++) if (v.nOn[i] && !N[i]!.extended) vis.push(i);
  return vis;
}

export function origem(): string {
  return extended.visible
    ? `<p class="mu sm">Indicadores da rede principal do IMC. Os ${fmt(EXTENDED_NODES)} pesquisadores sem colaboração com o IMC aparecem no grafo, mas não entram nestas contagens.</p>`
    : '';
}

export function porInstituto(v: View, vis: number[]): string {
  const byInst = new Map<string, number>();
  vis.forEach((i) => { const s = N[i]!.inst; byInst.set(s, (byInst.get(s) ?? 0) + 1); });
  const inst = [...byInst.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return `<h2>Pesquisadores por instituto</h2>
  ${inst.length ? bars(inst.map(([s, c]) => ({ label: s, color: col(s), value: c, frac: c / v.stats.nodes }))) : '<span class="mu">Nenhum pesquisador visível.</span>'}`;
}

export function summaryView(): string {
  const v = getView();
  const vis = visiveis(v);
  const top = [...vis].sort((a, b) => v.deg[b]! - v.deg[a]! || v.vol[b]! - v.vol[a]!).slice(0, 5).filter((i) => v.deg[i]! > 0);

  return `<h1>Resumo do recorte atual</h1>${origem()}
  <h2>Mais conectados no recorte</h2>
  <div class="li">${top.length ? top.map((i, k) => personRow(k + 1, i, `<span class="cnt">${fmt(v.deg[i]!)}</span>`)).join('') : '<span class="mu">Nenhuma conexão com os filtros atuais.</span>'}</div>
  ${porInstituto(v, vis)}
  <p class="mu empty">Clique em um pesquisador ou em uma aresta para ver os detalhes.</p>`;
}
