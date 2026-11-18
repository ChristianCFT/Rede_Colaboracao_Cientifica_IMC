// Sliders com a mesma aparência: o simples ("Mín. de atividades em comum") e o duplo (janela temporal).
// A trilha e o preenchimento são elementos próprios para que os dois fiquem idênticos em qualquer navegador.
import { $, fmt } from '../../core/dom';
import { YMAX, YMIN } from '../../core/model';
import { emitSoon, filters, on } from '../../core/state';
import { getView } from '../../core/selectors';

const THUMB = 16;
const pos = (p: number): string => `calc(${p} * (100% - ${THUMB}px) + ${THUMB / 2}px)`;
const frac = (v: number, lo: number, hi: number): number => (hi > lo ? (v - lo) / (hi - lo) : 0);

/** Envolve um input range existente com trilha e preenchimento (slider simples). */
export function wrapSlider(input: HTMLInputElement): () => void {
  const wrap = document.createElement('div');
  wrap.className = 'sl';
  wrap.innerHTML = '<div class="trk"></div><div class="fill"></div>';
  input.replaceWith(wrap);
  wrap.appendChild(input);
  const fill = wrap.querySelector<HTMLElement>('.fill')!;
  const paint = (): void => {
    const p = frac(Number(input.value), Number(input.min), Number(input.max));
    fill.style.left = '0'; fill.style.width = pos(p);
  };
  input.addEventListener('input', paint);
  paint();
  return paint;
}

export function initTimeWindow(): void {
  const a = $<HTMLInputElement>('y0'), b = $<HTMLInputElement>('y1');
  const box = $('yr'), fill = $('yfill');
  box.classList.add('sl', 'dual');
  for (const i of [a, b]) { i.min = String(YMIN); i.max = String(YMAX); i.step = '1'; }
  $('ymin').textContent = String(YMIN); $('ymax').textContent = String(YMAX);

  const paint = (): void => {
    a.value = String(filters.yearFrom); b.value = String(filters.yearTo);
    $('y0v').textContent = String(filters.yearFrom); $('y1v').textContent = String(filters.yearTo);
    const p0 = frac(filters.yearFrom, YMIN, YMAX), p1 = frac(filters.yearTo, YMIN, YMAX);
    fill.style.left = pos(p0);
    fill.style.width = `calc(${p1 - p0} * (100% - ${THUMB}px))`;
    // Com as duas alças no mesmo ano, a que pode se mover fica por cima.
    a.style.zIndex = filters.yearFrom === filters.yearTo && filters.yearFrom > (YMIN + YMAX) / 2 ? '3' : '';
    a.setAttribute('aria-valuetext', `de ${filters.yearFrom}`); b.setAttribute('aria-valuetext', `até ${filters.yearTo}`);
  };
  a.addEventListener('input', () => { filters.yearFrom = Math.min(Number(a.value), filters.yearTo); paint(); emitSoon('filters'); });
  b.addEventListener('input', () => { filters.yearTo = Math.max(Number(b.value), filters.yearFrom); paint(); emitSoon('filters'); });
  // Clique na trilha move a alça mais próxima.
  box.addEventListener('pointerdown', (e) => {
    if (e.target === a || e.target === b) return;
    const r = box.getBoundingClientRect();
    const p = Math.max(0, Math.min(1, (e.clientX - r.left - THUMB / 2) / (r.width - THUMB)));
    const y = Math.round(YMIN + p * (YMAX - YMIN));
    if (Math.abs(y - filters.yearFrom) <= Math.abs(y - filters.yearTo)) filters.yearFrom = Math.min(y, filters.yearTo);
    else filters.yearTo = Math.max(y, filters.yearFrom);
    paint(); emitSoon('filters');
  });
  const count = (): void => {
    const w = getView().facets.win;
    $('ywin').textContent = `${fmt(w)} atividades`;
  };
  on('filters', () => { paint(); count(); });
  paint(); count();
}
