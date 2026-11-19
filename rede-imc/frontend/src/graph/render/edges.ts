// Arestas: cor por instituto ou área. Espessura pelas atividades em comum no recorte (modo contagem)
// ou pelo peso normalizado da colaboração (modo peso, com as arestas mais fortes desenhadas por cima).
import { E, GC, N, col } from '../../core/model';
import { escala } from '../../core/peso';
import type { View } from '../../core/selectors';
import { display } from '../../core/state';
import type { GEdge } from '../../core/types';
import { sx, sy } from '../interaction/camera';
import { isHighlighted } from './frame';
import type { Frame } from './frame';

function edgeColor(e: GEdge): string {
  const a = N[e.a]!, b = N[e.b]!;
  if (display.colorMode === 'area') {
    if (a.inst === 'IMC' && b.inst === 'IMC') return a.grp === b.grp ? GC[a.grp] ?? '#444' : GC['cross'] ?? '#444';
    return GC[(a.inst === 'IMC' ? a : b).grp] ?? '#444';
  }
  return col((a.inst === 'IMC' ? b : a).inst);
}

/** Modo peso: de 0,5 a 6 px, pela escala do peso (raiz de W / maior W da rede; a legenda usa a mesma). */
export const espessuraDoPeso = (w: number): number => 0.5 + 5.5 * escala(w);

const width = (f: Frame, e: GEdge): number => (display.peso
  ? espessuraDoPeso(f.view.fw[e.i]!)
  : Math.min(6, 0.5 + 0.7 * Math.log2(1 + f.view.fsum[e.i]!)));

// Ordem de desenho no modo peso: da mais fraca para a mais forte, recalculada só quando o recorte muda.
let ordem: { ver: number; lista: GEdge[] } = { ver: -1, lista: [] };
function porPeso(v: View): GEdge[] {
  if (ordem.ver !== v.ver) ordem = { ver: v.ver, lista: [...E].sort((p, q) => v.fw[p.i]! - v.fw[q.i]!) };
  return ordem.lista;
}

const offscreen = (f: Frame, x1: number, y1: number, x2: number, y2: number): boolean =>
  (x1 < 0 && x2 < 0) || (x1 > f.W && x2 > f.W) || (y1 < 0 && y2 < 0) || (y1 > f.H && y2 > f.H);

/** Desenha o fundo primeiro e as arestas destacadas por cima. */
export function drawEdges(f: Frame): void {
  const { ctx, view, focus } = f;
  const highlighted: GEdge[] = [];
  ctx.globalAlpha = focus.active ? 0.04 : 0.28;
  for (const e of display.peso ? porPeso(view) : E) {
    if (!view.eOn[e.i]) continue;
    if (focus.active && isHighlighted(focus, e)) { highlighted.push(e); continue; }
    const a = N[e.a]!, b = N[e.b]!, x1 = sx(a.x), y1 = sy(a.y), x2 = sx(b.x), y2 = sy(b.y);
    if (offscreen(f, x1, y1, x2, y2)) continue;
    ctx.strokeStyle = edgeColor(e);
    ctx.lineWidth = width(f, e);
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }
  ctx.globalAlpha = focus.hover ? 1 : 0.9;
  for (const e of highlighted) {
    const a = N[e.a]!, b = N[e.b]!;
    ctx.strokeStyle = edgeColor(e);
    ctx.lineWidth = width(f, e) * 1.4;
    ctx.beginPath(); ctx.moveTo(sx(a.x), sy(a.y)); ctx.lineTo(sx(b.x), sy(b.y)); ctx.stroke();
  }
}
