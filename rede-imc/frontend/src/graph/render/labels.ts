// rótulos: só pesquisadores do IMC. testa 4 posições em volta do nó e se colidir
// em todas não desenha (menos hover/seleção)
import { E, N } from '../../core/model';
import { display, selection } from '../../core/state';
import type { GNode } from '../../core/types';
import { sx, sy } from '../interaction/camera';
import type { Frame } from './frame';

interface Candidate { i: number; x: number; y: number; prio: number; force: boolean; text: string }
interface Placed { x: number; y: number; h: number; text: string; strong: boolean }

const FONT = '11px system-ui,-apple-system,"Segoe UI",sans-serif';
const FONT_STRONG = '600 12px system-ui,-apple-system,"Segoe UI",sans-serif';
const labelEnabled = (n: GNode): boolean => n.inst === 'IMC' && display.labelsImc;

function candidates(f: Frame): Candidate[] {
  const { view, focus } = f;
  const out: Candidate[] = [];
  const prio = (n: GNode): number => view.deg[n.i]!;
  const push = (i: number, force: boolean): void => {
    const n = N[i]!;
    if (!view.nOn[i] || !labelEnabled(n)) return;
    const x = sx(n.x), y = sy(n.y);
    if (!force && (x < -40 || y < -20 || x > f.W + 40 || y > f.H + 20)) return;
    out.push({ i, x, y, prio: force ? 1e9 : prio(n), force, text: n.name });
  };
  if (selection.hover >= 0) push(selection.hover, true);
  if (selection.node >= 0) push(selection.node, true);
  if (focus.edge >= 0) { push(E[focus.edge]!.a, true); push(E[focus.edge]!.b, true); }
  if (focus.active) {
    for (const n of N) if (focus.near[n.i]) push(n.i, false);
  } else {
    for (const n of N) push(n.i, false);
  }
  return out;
}

const widths = new Map<string, number>();
function textWidth(ctx: CanvasRenderingContext2D, text: string, strong: boolean): number {
  const key = (strong ? 'b|' : 'n|') + text;
  let w = widths.get(key);
  if (w === undefined) { ctx.font = strong ? FONT_STRONG : FONT; w = ctx.measureText(text).width; widths.set(key, w); }
  return w;
}

const CELL = 96;
function place(f: Frame, cands: Candidate[]): Placed[] {
  cands.sort((a, b) => Number(b.force) - Number(a.force) || b.prio - a.prio);
  const grid = new Map<number, number[]>();
  const boxes: number[] = [];
  const out: Placed[] = [];
  const cells = (x0: number, y0: number, x1: number, y1: number, fn: (key: number) => boolean | void): boolean => {
    for (let cx = Math.floor(x0 / CELL); cx <= Math.floor(x1 / CELL); cx++)
      for (let cy = Math.floor(y0 / CELL); cy <= Math.floor(y1 / CELL); cy++)
        if (fn((cx + 1024) * 4096 + (cy + 1024)) === true) return true;
    return false;
  };
  const hits = (x0: number, y0: number, x1: number, y1: number): boolean => cells(x0, y0, x1, y1, (key) => {
    const list = grid.get(key);
    if (!list) return false;
    for (const b of list) {
      if (x0 < boxes[b + 2]! && x1 > boxes[b]! && y0 < boxes[b + 3]! && y1 > boxes[b + 1]!) return true;
    }
    return false;
  });
  const add = (x0: number, y0: number, x1: number, y1: number): void => {
    const b = boxes.length;
    boxes.push(x0, y0, x1, y1);
    cells(x0, y0, x1, y1, (key) => { let l = grid.get(key); if (!l) { l = []; grid.set(key, l); } l.push(b); });
  };
  const seen = new Set<number>();
  for (const c of cands) {
    if (seen.has(c.i)) continue;
    seen.add(c.i);
    const strong = c.force;
    const w = textWidth(f.ctx, c.text, strong), h = strong ? 15 : 13, pad = 2;
    const opts: [number, number][] = [
      [c.x + f.r + 4, c.y - h / 2], [c.x - f.r - 4 - w, c.y - h / 2],
      [c.x - w / 2, c.y - f.r - 2 - h], [c.x - w / 2, c.y + f.r + 2],
    ];
    let done = false;
    for (const [x, y] of opts) {
      if (!c.force && (x < 2 || y < 2 || x + w > f.W - 2 || y + h > f.H - 2)) continue;
      if (hits(x - pad, y - pad, x + w + pad, y + h + pad)) continue;
      add(x - pad, y - pad, x + w + pad, y + h + pad);
      out.push({ x, y, h, text: c.text, strong }); done = true; break;
    }
    if (!done && c.force) {
      const [x, y] = opts[0]!;
      add(x - pad, y - pad, x + w + pad, y + h + pad);
      out.push({ x, y, h, text: c.text, strong });
    }
  }
  return out;
}

export function drawLabels(f: Frame): void {
  const { ctx } = f;
  ctx.globalAlpha = 1; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (const p of place(f, candidates(f))) {
    ctx.font = p.strong ? FONT_STRONG : FONT;
    const y = p.y + p.h / 2;
    ctx.lineWidth = 3; ctx.strokeStyle = f.theme.bg; ctx.strokeText(p.text, p.x, y);
    ctx.fillStyle = f.theme.tx; ctx.fillText(p.text, p.x, y);
  }
}
