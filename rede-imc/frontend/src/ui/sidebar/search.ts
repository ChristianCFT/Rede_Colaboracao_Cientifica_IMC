// busca por nome
import { $, esc } from '../../core/dom';
import { N } from '../../core/model';
import { extended } from '../../core/state';
import { getView } from '../../core/selectors';
import { pickNode } from '../../graph/interaction/selection';

export function initSearch(): void {
  const q = $<HTMLInputElement>('q'), r = $('res');
  let hits: number[] = [], cur = -1;
  const choose = (i: number): void => { pickNode(i, true); r.innerHTML = ''; q.value = ''; hits = []; cur = -1; };
  const paint = (): void => {
    const v = getView();
    r.innerHTML = hits.map((i, k) => {
      const n = N[i]!, out = !v.nOn[i];
      return `<div data-n="${i}" role="option"${k === cur ? ' class="on" aria-selected="true"' : ''}>${esc(n.name)} <span class="mu">· ${esc(n.inst)}${out ? ' · fora do recorte' : ''}</span></div>`;
    }).join('');
    r.querySelectorAll<HTMLElement>('div').forEach((d) => { d.onclick = () => choose(Number(d.dataset['n'])); });
  };
  q.addEventListener('input', () => {
    const t = q.value.trim().toLowerCase();
    cur = -1;
    hits = t.length < 2 ? [] : N.filter((n) => (!n.extended || extended.visible) && n.name.toLowerCase().includes(t))
      .sort((a, b) => b.deg - a.deg).slice(0, 8).map((n) => n.i);
    paint();
  });
  q.addEventListener('keydown', (e) => {
    if (!hits.length) return;
    if (e.key === 'ArrowDown') { cur = (cur + 1) % hits.length; paint(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { cur = (cur - 1 + hits.length) % hits.length; paint(); e.preventDefault(); }
    else if (e.key === 'Enter') { choose(hits[Math.max(cur, 0)]!); e.preventDefault(); }
    else if (e.key === 'Escape') { hits = []; r.innerHTML = ''; }
  });
}
