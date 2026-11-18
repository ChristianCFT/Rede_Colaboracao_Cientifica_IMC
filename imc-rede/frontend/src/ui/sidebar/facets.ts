// Listas de filtro (bolinha + nome + contador) com checkbox mestre tri-state.
// Contadores seguem a lógica de busca facetada: cada lista ignora o próprio filtro e aplica os demais,
// então um item desmarcado continua mostrando quanto ele traria de volta.
import { $, esc, fmt } from '../../core/dom';
import { DIM_LONG, GC, col, dimCol } from '../../core/model';
import { dimOn, emit, grpOn, on, typeOn } from '../../core/state';
import { getCut } from '../../core/selectors';

interface Item { key: string; label: string; color: string }
interface FacetDef {
  box: string; master?: string; items: Item[]; unit: string;
  get: (k: string) => boolean; set: (k: string, v: boolean) => void;
}

function facet(def: FacetDef): (counts: Record<string, number>) => void {
  const box = $(def.box);
  box.innerHTML = def.items.map((it) =>
    `<label class="r" data-k="${esc(it.key)}"><input type="checkbox" data-k="${esc(it.key)}"><span class="sw" style="background:${it.color}"></span><span>${esc(it.label)}</span><span class="cnt" title="${esc(def.unit)}"></span></label>`,
  ).join('');
  const rows = def.items.map((it) => {
    const row = box.querySelector<HTMLElement>(`label[data-k="${CSS.escape(it.key)}"]`)!;
    return { it, row, input: row.querySelector<HTMLInputElement>('input')!, cnt: row.querySelector<HTMLElement>('.cnt')! };
  });
  rows.forEach(({ it, input }) => { input.addEventListener('change', () => { def.set(it.key, input.checked); emit('filters'); }); });
  const master = def.master ? $<HTMLInputElement>(def.master) : null;
  master?.addEventListener('change', () => {
    const all = def.items.every((it) => def.get(it.key));
    def.items.forEach((it) => def.set(it.key, !all));
    emit('filters');
  });
  return (counts) => {
    let onCount = 0;
    rows.forEach(({ it, row, input, cnt }) => {
      const c = counts[it.key] ?? 0;
      cnt.textContent = fmt(c);
      row.classList.toggle('zero', c === 0);
      input.checked = def.get(it.key);
      if (input.checked) onCount++;
    });
    if (master) {
      master.checked = onCount === rows.length;
      master.indeterminate = onCount > 0 && onCount < rows.length;
    }
  };
}

export function initFacets(): void {
  const upDims = facet({
    box: 'dims', unit: 'Atividades distintas no recorte',
    items: DIM_LONG.map((label, j) => ({ key: String(j), label, color: dimCol(j) })),
    get: (k) => !!dimOn[Number(k)], set: (k, v) => { dimOn[Number(k)] = v; },
  });
  const upTypes = facet({
    box: 'types', master: 'typesAll', unit: 'Arestas no recorte',
    items: Object.keys(typeOn).map((t) => ({ key: t, label: t, color: col(t.replace('IMC-', '')) })),
    get: (k) => !!typeOn[k], set: (k, v) => { typeOn[k] = v; },
  });
  const upGrps = facet({
    box: 'grps', master: 'grpsAll', unit: 'Pesquisadores do IMC com conexões no recorte',
    items: Object.keys(grpOn).map((g) => ({ key: g, label: g, color: GC[g] ?? '#444' })),
    get: (k) => !!grpOn[k], set: (k, v) => { grpOn[k] = v; },
  });
  const update = (): void => {
    const f = getCut().facets;
    upDims(Object.fromEntries(f.dims.map((c, j) => [String(j), c])));
    upTypes(f.types);
    upGrps(f.grps);
  };
  on('filters', update);
  update();
}
