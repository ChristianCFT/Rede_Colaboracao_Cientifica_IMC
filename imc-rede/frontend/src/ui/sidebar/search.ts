// Busca por nome + botão "Isolar rede (1º e 2º graus)" para o pesquisador selecionado.
import { $, esc, fmt } from '../../core/dom';
import { N } from '../../core/model';
import { S, on } from '../../core/state';
import { getView } from '../../core/selectors';
import { pickNode, setEgo } from '../../core/actions';

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
    hits = t.length < 2 ? [] : N.filter((n) => n.name.toLowerCase().includes(t)).sort((a, b) => b.deg - a.deg).slice(0, 8).map((n) => n.i);
    paint();
  });
  q.addEventListener('keydown', (e) => {
    if (!hits.length) return;
    if (e.key === 'ArrowDown') { cur = (cur + 1) % hits.length; paint(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { cur = (cur - 1 + hits.length) % hits.length; paint(); e.preventDefault(); }
    else if (e.key === 'Enter') { choose(hits[Math.max(cur, 0)]!); e.preventDefault(); }
    else if (e.key === 'Escape') { hits = []; r.innerHTML = ''; }
  });

  // Modo ego: aparece apenas com um pesquisador selecionado.
  const box = $('egoBox'), btn = $<HTMLButtonElement>('ego'), info = $('egoInfo');
  btn.addEventListener('click', () => setEgo(!S.ego));
  const sync = (): void => {
    box.hidden = S.sel < 0;
    if (S.sel < 0) return;
    btn.setAttribute('aria-pressed', String(S.ego));
    const v = getView(), n = N[S.sel]!;
    info.innerHTML = S.ego && v.ego
      ? `<span class="num">${fmt(v.ego.size)}</span> pesquisadores até 2 passos de <b>${esc(n.name)}</b>`
      : S.ego ? `<b>${esc(n.name)}</b> está fora do recorte atual` : `Vizinhança de <b>${esc(n.name)}</b>`;
  };
  on('selection', sync); on('filters', sync);
  sync();
}
