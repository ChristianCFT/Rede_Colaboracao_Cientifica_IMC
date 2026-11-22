// laço de desenho: arestas → nós → rótulos
import { $ } from '../../core/dom';
import { camera, on } from '../../core/state';
import { getView } from '../../core/selectors';
import { drawEdges } from './edges';
import { computeFocus } from './frame';
import type { Theme } from './frame';
import { drawLabels } from './labels';
import { drawNodes, nodeRadius } from './nodes';

export const cv = $<HTMLCanvasElement>('cv');
const ctx = cv.getContext('2d')!;

// cores do tema (variáveis CSS)
let theme: Theme = { tx: '#e6e8ee', bg: '#121212' };
function readTheme(): void {
  const cs = getComputedStyle(document.documentElement);
  theme = { tx: cs.getPropertyValue('--lab').trim() || '#fff', bg: cs.getPropertyValue('--cv').trim() || '#121212' };
}

function draw(): void {
  const view = getView(), W = camera.W, H = camera.H;
  ctx.setTransform(camera.dpr, 0, 0, camera.dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  const frame = { ctx, W, H, view, focus: computeFocus(view), theme, r: nodeRadius() };
  drawEdges(frame);
  drawNodes(frame);
  drawLabels(frame);
}

let pending = 0;
function requestDraw(): void {
  if (!pending) pending = requestAnimationFrame(() => { pending = 0; draw(); });
}

export function resize(): void {
  const r = cv.parentElement!.getBoundingClientRect();
  camera.W = r.width; camera.H = r.height; camera.dpr = window.devicePixelRatio || 1;
  cv.width = Math.round(camera.W * camera.dpr); cv.height = Math.round(camera.H * camera.dpr); draw();
}

/** o canvas é transparente, então pinta o fundo antes */
export function exportPNG(name = 'grafo_IMC.png'): void {
  const out = document.createElement('canvas');
  out.width = cv.width; out.height = cv.height;
  const o = out.getContext('2d')!;
  o.fillStyle = theme.bg; o.fillRect(0, 0, out.width, out.height); o.drawImage(cv, 0, 0);
  out.toBlob((b) => {
    if (!b) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
}

export function initRender(): void {
  readTheme();
  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', () => { readTheme(); requestDraw(); });
  on('filters', requestDraw); on('selection', requestDraw); on('view', requestDraw); on('peso', requestDraw);
  window.addEventListener('resize', resize);
}
