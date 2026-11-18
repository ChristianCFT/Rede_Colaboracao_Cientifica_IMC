// Subtítulo da sidebar: mostra a base completa ou os filtros ativos, com atalho para limpá-los.
import { $, fmt } from '../../core/dom';
import { E, N } from '../../core/model';
import { S, dimOn, grpOn, on, resetFilters, typeOn, yearFull } from '../../core/state';

function active(): string[] {
  const out: string[] = [];
  const k = (r: Record<string, boolean> | boolean[]): [number, number] => {
    const v = Object.values(r);
    return [v.filter(Boolean).length, v.length];
  };
  const [d, dn] = k(dimOn); if (d < dn) out.push(`${d} de ${dn} dimensões`);
  if (!yearFull()) out.push(`${S.y0}–${S.y1}`);
  const [t, tn] = k(typeOn); if (t < tn) out.push(`${t} de ${tn} tipos`);
  const [g, gn] = k(grpOn); if (g < gn) out.push(`${g} de ${gn} áreas`);
  if (S.minS > 1) out.push(`mín. ${S.minS} atividades`);
  if (!S.showExt) out.push('sem externos');
  if (S.ego) out.push('rede isolada');
  return out;
}

export function initFilterSummary(): void {
  const el = $('stats');
  const paint = (): void => {
    const a = active();
    if (!a.length) { el.textContent = `${fmt(N.length)} pesquisadores · ${fmt(E.length)} arestas (não direcionadas)`; return; }
    el.innerHTML = `Filtros: ${a.join(' · ')} · <button type="button" class="lnk" id="clr">Limpar</button>`;
    $('clr').addEventListener('click', () => resetFilters());
  };
  on('filters', paint); on('selection', paint);
  paint();
}
