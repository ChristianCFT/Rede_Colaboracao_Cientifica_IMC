// Arestas: cor por instituto ou área.
// Modo contagem: espessura leve pelas atividades em comum no recorte, todas com a mesma opacidade.
// Modo peso: a força da relação (peso ÷ maior peso da rede) define a espessura e a opacidade ao mesmo
// tempo; as relações fracas ficam finas e claras, as fortes grossas e quase sólidas, desenhadas por cima.
import { E, GC, N, col } from '../../core/model';
import { escala } from '../../core/peso';
import type { View } from '../../core/selectors';
import { camera, display } from '../../core/state';
import type { GEdge } from '../../core/types';
import { sx, sy } from '../interaction/camera';
import { isHighlighted } from './frame';
import type { Frame } from './frame';

// Modo contagem.
const OPACIDADE_CONTAGEM = 0.28;

// Modo peso: contraste entre relações fracas e fortes (intermediário: nem suave, nem forte).
const ESPESSURA_MIN = 0.6;    // px da relação mais fraca, com zoom 1:1
const ESPESSURA_MAX = 7;      // px da relação mais forte da rede
const OPACIDADE_MIN = 0.14;   // relação mais fraca: bem clara
const OPACIDADE_MAX = 0.86;   // relação mais forte: quase sólida
const CURVA_OPACIDADE = 0.8;  // abaixo de 1, as relações médias ficam um pouco mais visíveis
const ZOOM_MAXIMO = 2;        // ao aproximar, as arestas engrossam até 2x, como os nós

// Com um nó ou uma aresta em destaque, o resto da rede quase some (nos dois modos).
const OPACIDADE_FORA_DO_FOCO = 0.04;

function edgeColor(e: GEdge): string {
  const a = N[e.a]!, b = N[e.b]!;
  if (display.colorMode === 'area') {
    if (a.inst === 'IMC' && b.inst === 'IMC') return a.grp === b.grp ? GC[a.grp] ?? '#444' : GC['cross'] ?? '#444';
    return GC[(a.inst === 'IMC' ? a : b).grp] ?? '#444';
  }
  return col((a.inst === 'IMC' ? b : a).inst);
}

/** Modo contagem: de 0,5 a 6 px pelo log das atividades em comum no recorte. */
const espessuraDaContagem = (n: number): number => Math.min(6, 0.5 + 0.7 * Math.log2(1 + n));

/** Modo peso: espessura em px (zoom 1:1) para uma força de 0 a 1 (a legenda usa a mesma). */
export const espessura = (s: number): number => ESPESSURA_MIN + (ESPESSURA_MAX - ESPESSURA_MIN) * s;

/** Modo peso: opacidade para uma força de 0 a 1 (a legenda usa a mesma). */
export const opacidade = (s: number): number => OPACIDADE_MIN + (OPACIDADE_MAX - OPACIDADE_MIN) * s ** CURVA_OPACIDADE;

/** Modo peso: ao aproximar, as arestas engrossam junto com os nós; ao afastar, ficam na espessura base. */
const fatorDoZoom = (): number => Math.min(ZOOM_MAXIMO, Math.max(1, Math.sqrt(camera.k * 2)));

/** Espessura (px) e opacidade de uma aresta no recorte, conforme o modo. */
function estilo(v: View, e: GEdge): [number, number] {
  if (!display.peso) return [espessuraDaContagem(v.fsum[e.i]!), OPACIDADE_CONTAGEM];
  const s = escala(v.fw[e.i]!);
  return [espessura(s) * fatorDoZoom(), opacidade(s)];
}

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
  for (const e of display.peso ? porPeso(view) : E) {
    if (!view.eOn[e.i]) continue;
    if (focus.active && isHighlighted(focus, e)) { highlighted.push(e); continue; }
    const a = N[e.a]!, b = N[e.b]!, x1 = sx(a.x), y1 = sy(a.y), x2 = sx(b.x), y2 = sy(b.y);
    if (offscreen(f, x1, y1, x2, y2)) continue;
    const [largura, op] = estilo(view, e);
    ctx.globalAlpha = focus.active ? OPACIDADE_FORA_DO_FOCO : op;
    ctx.strokeStyle = edgeColor(e);
    ctx.lineWidth = largura;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }
  ctx.globalAlpha = focus.hover ? 1 : 0.9;
  for (const e of highlighted) {
    const a = N[e.a]!, b = N[e.b]!;
    ctx.strokeStyle = edgeColor(e);
    ctx.lineWidth = estilo(view, e)[0] * 1.4;
    ctx.beginPath(); ctx.moveTo(sx(a.x), sy(a.y)); ctx.lineTo(sx(b.x), sy(b.y)); ctx.stroke();
  }
}
