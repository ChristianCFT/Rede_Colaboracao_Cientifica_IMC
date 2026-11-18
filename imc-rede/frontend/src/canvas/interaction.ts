// Zoom, pan, arrastar nós, hover (holofote + tooltip) e clique.
import { $, esc, fmt } from '../core/dom';
import { E, N } from '../core/model';
import { S, emit } from '../core/state';
import { getView } from '../core/selectors';
import { clearSelection, pickEdge, pickNode } from '../core/actions';
import { K_MAX, K_MIN, fitView, stopCamera, zoomBy } from './camera';
import { dragEnd, dragMove, dragStart } from './physics';
import { cv, rad, sx, sy } from './render';

function nodeAt(mx: number, my: number): number {
  const v = getView();
  let b = -1, bd = 1e9;
  for (const n of N) {
    if (!v.nOn[n.i]) continue;
    const d = Math.hypot(sx(n.x) - mx, sy(n.y) - my);
    if (d < rad(n.i) + 4 && d < bd) { bd = d; b = n.i; }
  }
  return b;
}
function edgeAt(mx: number, my: number): number {
  const v = getView();
  let b = -1, bd = 5;
  for (const e of E) {
    if (!v.eOn[e.i]) continue;
    const x1 = sx(N[e.a]!.x), y1 = sy(N[e.a]!.y), dx = sx(N[e.b]!.x) - x1, dy = sy(N[e.b]!.y) - y1;
    const t = Math.max(0, Math.min(1, ((mx - x1) * dx + (my - y1) * dy) / (dx * dx + dy * dy || 1)));
    const d = Math.hypot(mx - (x1 + t * dx), my - (y1 + t * dy));
    if (d < bd) { bd = d; b = e.i; }
  }
  return b;
}

export function initInteraction(): void {
  const tip = $('tip');
  type Drag = { mode: 'pan'; x: number; y: number; tx: number; ty: number } | { mode: 'node'; i: number; x: number; y: number };
  let drag: Drag | null = null, moved = 0;

  const hideTip = (): void => { tip.style.display = 'none'; };
  const showTip = (i: number, x: number, y: number): void => {
    const n = N[i]!, v = getView();
    tip.innerHTML = `<b>${esc(n.name)}</b><br><span class="mu">${esc(n.inst)} · <span class="num">${fmt(v.deg[i]!)}</span> parceiros no recorte</span>`;
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    tip.style.left = `${Math.min(x + 14, S.W - r.width - 8)}px`;
    tip.style.top = `${Math.min(y + 14, S.H - r.height - 8)}px`;
  };

  cv.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    stopCamera();
    cv.setPointerCapture(e.pointerId);
    moved = 0;
    const h = nodeAt(e.offsetX, e.offsetY);
    if (h >= 0) { drag = { mode: 'node', i: h, x: e.offsetX, y: e.offsetY }; }
    else { drag = { mode: 'pan', x: e.offsetX, y: e.offsetY, tx: S.tx, ty: S.ty }; cv.style.cursor = 'grabbing'; }
  });
  cv.addEventListener('pointerup', (e) => {
    if (drag?.mode === 'node' && moved > 4) dragEnd(drag.i);
    drag = null; cv.style.cursor = S.hov >= 0 ? 'pointer' : 'grab';
    if (cv.hasPointerCapture(e.pointerId)) cv.releasePointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', (e) => {
    if (drag) {
      const dx = e.offsetX - drag.x, dy = e.offsetY - drag.y;
      const was = moved;
      moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
      if (drag.mode === 'pan') { S.tx = drag.tx + dx; S.ty = drag.ty + dy; emit('view'); return; }
      if (moved > 4) {
        if (was <= 4) { dragStart(drag.i); cv.style.cursor = 'grabbing'; hideTip(); }
        dragMove(drag.i, (e.offsetX - S.tx) / S.k, (e.offsetY - S.ty) / S.k);
      }
      return;
    }
    const h = nodeAt(e.offsetX, e.offsetY);
    if (h !== S.hov) { S.hov = h; cv.style.cursor = h >= 0 ? 'pointer' : 'grab'; emit('view'); }
    if (h >= 0) showTip(h, e.offsetX, e.offsetY); else hideTip();
  });
  cv.addEventListener('pointerleave', () => { if (!drag) { S.hov = -1; hideTip(); emit('view'); } });
  cv.addEventListener('wheel', (e) => {
    e.preventDefault(); stopCamera();
    const nk = Math.max(K_MIN, Math.min(K_MAX, S.k * Math.exp(-e.deltaY * 0.0015)));
    S.tx = e.offsetX - ((e.offsetX - S.tx) * nk) / S.k; S.ty = e.offsetY - ((e.offsetY - S.ty) * nk) / S.k; S.k = nk;
    emit('view');
  }, { passive: false });
  cv.addEventListener('click', (e) => {
    if (moved > 4) return;
    const n = nodeAt(e.offsetX, e.offsetY); if (n >= 0) { pickNode(n); return; }
    const ed = edgeAt(e.offsetX, e.offsetY); if (ed >= 0) { pickEdge(ed); return; }
    clearSelection();
  });
  cv.addEventListener('dblclick', (e) => { if (nodeAt(e.offsetX, e.offsetY) < 0) fitView(); });

  // Atalhos de teclado (fora de campos de texto): Esc limpa a seleção, +/− zoom, F enquadra.
  window.addEventListener('keydown', (e) => {
    const t = e.target as HTMLElement | null;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.key === 'Escape') clearSelection();
    else if (e.key === '+' || e.key === '=') zoomBy(1.4);
    else if (e.key === '-') zoomBy(1 / 1.4);
    else if (e.key === 'f' || e.key === 'F') fitView();
  });
}
