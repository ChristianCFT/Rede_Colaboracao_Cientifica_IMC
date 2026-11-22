import { $, fmt } from '../../core/dom';
import { MAIN_EDGES, MAIN_NODES } from '../../core/model';
import { filters, fullYearRange, on, resetFilters } from '../../core/state';

function active(): string[] {
  const out: string[] = [];
  const count = (r: Record<string, boolean> | boolean[]): [number, number] => {
    const v = Object.values(r);
    return [v.filter(Boolean).length, v.length];
  };
  const [d, dn] = count(filters.dims); if (d < dn) out.push(`${d} de ${dn} dimensões`);
  if (!fullYearRange()) out.push(`${filters.yearFrom}–${filters.yearTo}`);
  const [t, tn] = count(filters.types); if (t < tn) out.push(`${t} de ${tn} tipos`);
  const [g, gn] = count(filters.groups); if (g < gn) out.push(`${g} de ${gn} áreas`);
  if (filters.minActivities > 1) out.push(`mín. ${filters.minActivities} atividades`);
  if (!filters.showExternal) out.push('sem externos');
  return out;
}

export function initFilterSummary(): void {
  const el = $('stats');
  const paint = (): void => {
    const a = active();
    if (!a.length) { el.textContent = `${fmt(MAIN_NODES)} pesquisadores · ${fmt(MAIN_EDGES)} Arestas`; return; }
    el.innerHTML = `Filtros: ${a.join(' · ')} · <button type="button" class="lnk" id="clr">Limpar</button>`;
    $('clr').addEventListener('click', () => resetFilters());
  };
  on('filters', paint);
  paint();
}
