import { GC, N, col } from '../../core/model';
import { camera, display, selection } from '../../core/state';
import type { GNode } from '../../core/types';
import { sx, sy } from '../interaction/camera';
import type { Frame } from './frame';

/** px com zoom 1:1 */
export const NODE_RADIUS = 5;

export const nodeRadius = (): number => NODE_RADIUS * Math.min(2, Math.max(0.7, Math.sqrt(camera.k * 2)));

const nodeColor = (n: GNode): string =>
  (display.colorMode === 'area' && n.inst === 'IMC' ? GC[n.grp] ?? '#444' : col(n.inst));

export function drawNodes(f: Frame): void {
  const { ctx, view, focus, r } = f;
  const draw = (n: GNode): void => {
    const x = sx(n.x), y = sy(n.y);
    if (x < -r || y < -r || x > f.W + r || y > f.H + r) return;
    ctx.fillStyle = nodeColor(n);
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
    if (n.i === selection.node || n.i === selection.hover) { ctx.lineWidth = 2; ctx.strokeStyle = f.theme.tx; ctx.stroke(); }
  };
  ctx.globalAlpha = focus.active ? 0.1 : 1;
  for (const n of N) if (view.nOn[n.i] && !(focus.active && focus.near[n.i])) draw(n);
  if (focus.active) { ctx.globalAlpha = 1; for (const n of N) if (view.nOn[n.i] && focus.near[n.i]) draw(n); }
}
