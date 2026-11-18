// Sliders com a mesma aparência: o simples ("Mín. de atividades em comum") e o duplo (janela temporal).
// A trilha e o preenchimento são elementos próprios para que os dois fiquem idênticos em qualquer navegador.
import { $, fmt } from '../../core/dom';
import { YMAX, YMIN } from '../../core/model';
import { S, emitSoon, on } from '../../core/state';
import { getCut } from '../../core/selectors';

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
    a.value = String(S.y0); b.value = String(S.y1);
    $('y0v').textContent = String(S.y0); $('y1v').textContent = String(S.y1);
    const p0 = frac(S.y0, YMIN, YMAX), p1 = frac(S.y1, YMIN, YMAX);
    fill.style.left = pos(p0);
    fill.style.width = `calc(${p1 - p0} * (100% - ${THUMB}px))`;
    // Com as duas alças no mesmo ano, a que pode se mover fica por cima.
    a.style.zIndex = S.y0 === S.y1 && S.y0 > (YMIN + YMAX) / 2 ? '3' : '';
    a.setAttribute('aria-valuetext', `de ${S.y0}`); b.setAttribute('aria-valuetext', `até ${S.y1}`);
  };
  a.addEventListener('input', () => { S.y0 = Math.min(Number(a.value), S.y1); paint(); emitSoon('filters'); });
  b.addEventListener('input', () => { S.y1 = Math.max(Number(b.value), S.y0); paint(); emitSoon('filters'); });
  // Clique na trilha move a alça mais próxima.
  box.addEventListener('pointerdown', (e) => {
    if (e.target === a || e.target === b) return;
    const r = box.getBoundingClientRect();
    const p = Math.max(0, Math.min(1, (e.clientX - r.left - THUMB / 2) / (r.width - THUMB)));
    const y = Math.round(YMIN + p * (YMAX - YMIN));
    if (Math.abs(y - S.y0) <= Math.abs(y - S.y1)) S.y0 = Math.min(y, S.y1); else S.y1 = Math.max(y, S.y0);
    paint(); emitSoon('filters');
  });
  const count = (): void => {
    const w = getCut().facets.win;
    $('ywin').textContent = `${fmt(w)} atividades`;
  };
  on('filters', () => { paint(); count(); });
  paint(); count();
}
