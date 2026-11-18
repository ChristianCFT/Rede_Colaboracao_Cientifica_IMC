// Motor de renderização do grafo (canvas 2D).
// - Holofote: com o mouse sobre um nó, ele, os vizinhos diretos e as arestas entre eles ficam em 100%
//   e o restante cai para ~10%; com um nó selecionado (sem hover), o mesmo foco vale para a seleção.
// - Rótulos: zoom semântico (quem aparece depende do zoom e do tamanho) + colisão de bounding box.
import { $ } from '../core/dom';
import { E, GC, N, col } from '../core/model';
import { S, on } from '../core/state';
import { baseRadii, getView } from '../core/selectors';
import type { GEdge, GNode } from '../types/graph';
import { FONT, FONT_STRONG, placeLabels } from './labels';
import type { LabelCand } from './labels';

export const cv = $<HTMLCanvasElement>('cv');
const ctx = cv.getContext('2d')!;

export const sx = (x: number): number => x * S.k + S.tx;
export const sy = (y: number): number => y * S.k + S.ty;
/** Fator de zoom aplicado ao raio (o mesmo do projeto original). */
const zf = (): number => Math.min(2, Math.max(0.7, Math.sqrt(S.k * 2)));
export const rad = (i: number): number => baseRadii()[i]! * zf();

const nodeCol = (n: GNode): string => (S.colorMode === 'area' && n.inst === 'IMC' ? GC[n.grp] ?? '#444' : col(n.inst));
function edgeCol(e: GEdge): string {
  const a = N[e.a]!, b = N[e.b]!;
  if (S.colorMode === 'area') {
    if (a.inst === 'IMC' && b.inst === 'IMC') return a.grp === b.grp ? GC[a.grp] ?? '#444' : GC['cross'] ?? '#444';
    return GC[(a.inst === 'IMC' ? a : b).grp] ?? '#444';
  }
  return col((a.inst === 'IMC' ? b : a).inst);
}

// Cores do tema lidas das variáveis CSS (atualizadas quando o esquema de cores do sistema muda).
let theme = { tx: '#e6e8ee', bg: '#121212' };
function readTheme(): void {
  const cs = getComputedStyle(document.documentElement);
  theme = { tx: cs.getPropertyValue('--lab').trim() || '#fff', bg: cs.getPropertyValue('--cv').trim() || '#121212' };
}
export const canvasBg = (): string => theme.bg;

let pending = 0;
export function requestDraw(): void {
  if (!pending) pending = requestAnimationFrame(() => { pending = 0; draw(); });
}

export function resize(): void {
  const r = cv.parentElement!.getBoundingClientRect();
  S.W = r.width; S.H = r.height; S.dpr = window.devicePixelRatio || 1;
  cv.width = Math.round(S.W * S.dpr); cv.height = Math.round(S.H * S.dpr); draw();
}

let nb = new Uint8Array(0);

export function draw(): void {
  const v = getView(), R = baseRadii(), z = zf(), W = S.W, H = S.H;
  ctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  if (nb.length !== N.length) nb = new Uint8Array(N.length); else nb.fill(0);

  // Centro do foco: hover tem prioridade sobre a seleção.
  let fc = -1, fe = -1;
  const hover = S.hov >= 0 && v.nOn[S.hov] === 1;
  if (hover) fc = S.hov;
  else if (S.sel >= 0 && v.nOn[S.sel]) fc = S.sel;
  else if (S.selE >= 0 && v.eOn[S.selE]) fe = S.selE;
  if (fc >= 0) { nb[fc] = 1; for (const j of N[fc]!.adj) if (v.eOn[j]) { nb[E[j]!.a] = 1; nb[E[j]!.b] = 1; } }
  if (fe >= 0) { nb[E[fe]!.a] = 1; nb[E[fe]!.b] = 1; }
  const focus = fc >= 0 || fe >= 0;
  // No modo ego (sem hover) o 2º grau continua legível: apagamento intermediário em vez de ~10%.
  const egoSoft = focus && !hover && S.ego && fc === S.sel;
  const dimNode = egoSoft ? 0.45 : 0.1, dimEdge = egoSoft ? 0.16 : 0.04;
  const isHi = (e: GEdge): boolean => (fc >= 0 && (e.a === fc || e.b === fc)) || e.i === fe;

  // Arestas: fundo primeiro, destacadas por cima.
  const fs = v.cut.fsum;
  const off = (x1: number, y1: number, x2: number, y2: number): boolean =>
    (x1 < 0 && x2 < 0) || (x1 > W && x2 > W) || (y1 < 0 && y2 < 0) || (y1 > H && y2 > H);
  const hiList: GEdge[] = [];
  ctx.globalAlpha = focus ? dimEdge : 0.28;
  for (const e of E) {
    if (!v.eOn[e.i]) continue;
    if (focus && isHi(e)) { hiList.push(e); continue; }
    const a = N[e.a]!, b = N[e.b]!, x1 = sx(a.x), y1 = sy(a.y), x2 = sx(b.x), y2 = sy(b.y);
    if (off(x1, y1, x2, y2)) continue;
    ctx.strokeStyle = edgeCol(e);
    ctx.lineWidth = Math.min(6, 0.5 + 0.7 * Math.log2(1 + fs[e.i]!));
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }
  ctx.globalAlpha = hover ? 1 : 0.9;
  for (const e of hiList) {
    const a = N[e.a]!, b = N[e.b]!;
    ctx.strokeStyle = edgeCol(e);
    ctx.lineWidth = Math.min(6, 0.5 + 0.7 * Math.log2(1 + fs[e.i]!)) * 1.4;
    ctx.beginPath(); ctx.moveTo(sx(a.x), sy(a.y)); ctx.lineTo(sx(b.x), sy(b.y)); ctx.stroke();
  }

  // Nós: os apagados primeiro, os do foco por cima.
  const drawNode = (n: GNode): void => {
    const x = sx(n.x), y = sy(n.y), r = R[n.i]! * z;
    if (x < -r || y < -r || x > W + r || y > H + r) return;
    ctx.fillStyle = nodeCol(n);
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
    if (n.i === S.sel || n.i === S.hov) { ctx.lineWidth = 2; ctx.strokeStyle = theme.tx; ctx.stroke(); }
  };
  ctx.globalAlpha = focus ? dimNode : 1;
  for (const n of N) if (v.nOn[n.i] && !(focus && nb[n.i])) drawNode(n);
  if (focus) { ctx.globalAlpha = 1; for (const n of N) if (v.nOn[n.i] && nb[n.i]) drawNode(n); }

  // Rótulos.
  const cands: LabelCand[] = [];
  const push = (i: number, prio: number, force: boolean): void => {
    const n = N[i]!;
    if (!v.nOn[i]) return;
    const x = sx(n.x), y = sy(n.y);
    if (!force && (x < -40 || y < -20 || x > W + 40 || y > H + 20)) return;
    cands.push({ i, x, y, r: R[i]! * z, prio, force, text: n.name });
  };
  if (S.hov >= 0) push(S.hov, 1e9, true);
  if (S.sel >= 0) push(S.sel, 1e9, true);
  if (fe >= 0) { push(E[fe]!.a, 1e9, true); push(E[fe]!.b, 1e9, true); }
  if (focus) {
    for (const n of N) if (nb[n.i]) push(n.i, R[n.i]! + (n.inst === 'IMC' ? 60 : 0), false);
    if (egoSoft && S.showLab) for (const n of N) if (!nb[n.i] && n.inst === 'IMC') push(n.i, R[n.i]!, false);
  } else {
    const semantic = S.k >= 0.8;
    for (const n of N) {
      if (!v.nOn[n.i]) continue;
      const r = R[n.i]! * z;
      if (S.showLab && n.inst === 'IMC') push(n.i, 1000 + R[n.i]!, false);
      else if (semantic || r >= 10) push(n.i, R[n.i]!, false);
    }
  }
  const placed = placeLabels(ctx, cands, W, H);
  ctx.globalAlpha = 1; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (const p of placed) {
    ctx.font = p.strong ? FONT_STRONG : FONT;
    const y = p.y + p.h / 2;
    ctx.lineWidth = 3; ctx.strokeStyle = theme.bg; ctx.strokeText(p.text, p.x, y);
    ctx.fillStyle = theme.tx; ctx.fillText(p.text, p.x, y);
  }
}

/** Exporta a imagem do canvas com o fundo do tema (o canvas em si é transparente). */
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
  on('filters', requestDraw); on('selection', requestDraw); on('view', requestDraw);
  window.addEventListener('resize', resize);
}
