// Câmera: zoom, enquadramento e centralização animados (interpolação do centro e de log(k)).
import { N } from '../core/model';
import { S, emit } from '../core/state';
import { getView } from '../core/selectors';

export const K_MIN = 0.02;
export const K_MAX = 20;
const clampK = (k: number): number => Math.max(K_MIN, Math.min(K_MAX, k));
const reduced = (): boolean => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

let raf = 0;
/** Anima até o zoom k com o ponto do mundo (cx, cy) no centro da tela. */
export function animateTo(k: number, cx: number, cy: number, ms = 320): void {
  cancelAnimationFrame(raf);
  k = clampK(k);
  const k0 = S.k, c0x = (S.W / 2 - S.tx) / S.k, c0y = (S.H / 2 - S.ty) / S.k;
  const apply = (kk: number, x: number, y: number): void => { S.k = kk; S.tx = S.W / 2 - kk * x; S.ty = S.H / 2 - kk * y; emit('view'); };
  if (ms <= 0 || reduced()) { apply(k, cx, cy); return; }
  const t0 = performance.now(), l0 = Math.log(k0), l1 = Math.log(k);
  const step = (t: number): void => {
    const p = Math.min(1, (t - t0) / ms), e = 1 - (1 - p) ** 3;
    apply(Math.exp(l0 + (l1 - l0) * e), c0x + (cx - c0x) * e, c0y + (cy - c0y) * e);
    if (p < 1) raf = requestAnimationFrame(step);
  };
  raf = requestAnimationFrame(step);
}

export function stopCamera(): void { cancelAnimationFrame(raf); }

/** Zoom a partir do centro da tela. */
export function zoomBy(f: number): void {
  animateTo(S.k * f, (S.W / 2 - S.tx) / S.k, (S.H / 2 - S.ty) / S.k, 220);
}

/** Enquadra os nós visíveis (ou as posições de repouso, durante uma transição de layout). */
export function fitView(ms = 380, useAnchors = false): void {
  const v = getView();
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, n = 0;
  N.forEach((p) => {
    if (!v.nOn[p.i]) return;
    const x = useAnchors ? p.ax : p.x, y = useAnchors ? p.ay : p.y;
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); n++;
  });
  if (!n) return;
  // Margem para o HUD (topo) e para os controles (canto inferior direito).
  const padX = 70, padTop = 86, padBot = 40;
  const w = Math.max(x1 - x0, 1), h = Math.max(y1 - y0, 1);
  let k = Math.min((S.W - 2 * padX) / w, (S.H - padTop - padBot) / h);
  if (n === 1) k = Math.max(S.k, 1);
  k = Math.min(k, 3);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2 - (padTop - padBot) / 2 / k;
  animateTo(k, cx, cy, ms);
}

/** Centraliza um nó mantendo o zoom atual. */
export function centerOn(i: number): void {
  const n = N[i];
  if (n) animateTo(S.k, n.x, n.y, 380);
}
