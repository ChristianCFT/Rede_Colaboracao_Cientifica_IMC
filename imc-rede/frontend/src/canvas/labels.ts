// Rotulagem inteligente: posicionamento guloso por prioridade com detecção de colisão de
// bounding boxes (grade espacial). Cada rótulo tenta 4 posições (direita, esquerda, acima,
// abaixo do nó); se todas colidem ele é omitido — exceto os "forçados" (hover/seleção).
export interface LabelCand { i: number; x: number; y: number; r: number; prio: number; force: boolean; text: string }
export interface Placed { i: number; x: number; y: number; w: number; h: number; text: string; strong: boolean }

export const FONT = '11px system-ui,-apple-system,"Segoe UI",sans-serif';
export const FONT_STRONG = '600 12px system-ui,-apple-system,"Segoe UI",sans-serif';

const widths = new Map<string, number>();
function textW(ctx: CanvasRenderingContext2D, text: string, strong: boolean): number {
  const key = (strong ? 'b|' : 'n|') + text;
  let w = widths.get(key);
  if (w === undefined) { ctx.font = strong ? FONT_STRONG : FONT; w = ctx.measureText(text).width; widths.set(key, w); }
  return w;
}

const CELL = 96;
export function placeLabels(ctx: CanvasRenderingContext2D, cands: LabelCand[], W: number, H: number): Placed[] {
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
    const w = textW(ctx, c.text, strong), h = strong ? 15 : 13, pad = 2;
    const opts: [number, number][] = [
      [c.x + c.r + 4, c.y - h / 2], [c.x - c.r - 4 - w, c.y - h / 2],
      [c.x - w / 2, c.y - c.r - 2 - h], [c.x - w / 2, c.y + c.r + 2],
    ];
    let done = false;
    for (const [x, y] of opts) {
      if (!c.force && (x < 2 || y < 2 || x + w > W - 2 || y + h > H - 2)) continue;
      if (hits(x - pad, y - pad, x + w + pad, y + h + pad)) continue;
      add(x - pad, y - pad, x + w + pad, y + h + pad);
      out.push({ i: c.i, x, y, w, h, text: c.text, strong }); done = true; break;
    }
    if (!done && c.force) {
      const [x, y] = opts[0]!;
      add(x - pad, y - pad, x + w + pad, y + h + pad);
      out.push({ i: c.i, x, y, w, h, text: c.text, strong });
    }
  }
  return out;
}
