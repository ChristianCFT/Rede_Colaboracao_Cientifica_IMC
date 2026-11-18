// Física leve (d3-force) sobre o layout pré-calculado pelo backend.
// Cada nó é atraído para a sua posição de repouso (ax, ay); colisão afasta nós sobrepostos e as
// arestas mantêm o comprimento original. Resultado: o desenho do NetworkX é preservado, o miolo
// fica menos encavalado e os nós podem ser arrastados. Pausar congela tudo onde está.
// Os pesquisadores sem colaboração com o IMC participam da mesma simulação: ficam ancorados no anel
// calculado pelo backend e não têm arestas, então ligá-los ou desligá-los não desloca a rede principal.
import { forceCollide, forceLink, forceSimulation, forceX, forceY } from 'd3-force';
import type { ForceX, ForceY, Simulation, SimulationLinkDatum } from 'd3-force';
import { E, N } from '../core/model';
import { display, emit } from '../core/state';
import type { GNode, LayoutMode } from '../core/types';
import { NODE_RADIUS } from './render/nodes';

interface Link extends SimulationLinkDatum<GNode> { d: number; w: number }

let sim: Simulation<GNode, Link> | null = null;
let fX: ForceX<GNode> | null = null;
let fY: ForceY<GNode> | null = null;
/** forceX/forceY guardam os alvos na inicialização: reaplica o acessor quando (ax, ay) mudam. */
const refreshAnchors = (): void => { fX?.x((n) => n.ax); fY?.y((n) => n.ay); };
let raf = 0;
let collideScale = 2.6;
let extentFree = 1;

/** Extensão da rede principal num layout (a escala de colisão acompanha o tamanho do desenho). */
const extent = (m: LayoutMode): number => {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  N.forEach((n) => {
    if (n.extended) return;
    const [x, y] = n.lay[m];
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  });
  return Math.max(x1 - x0, y1 - y0, 1);
};
/** Raio de colisão em unidades do mundo: o mesmo para todos os nós, como o tamanho desenhado. */
const collideRadius = (): number => NODE_RADIUS * collideScale;

function links(): Link[] {
  return E.map((e) => {
    const a = N[e.a]!, b = N[e.b]!;
    return { source: e.a, target: e.b, d: Math.hypot(a.ax - b.ax, a.ay - b.ay), w: 0.3 / Math.max(1, Math.min(a.deg, b.deg)) };
  });
}

export function initPhysics(): void {
  extentFree = extent('free');
  fX = forceX<GNode>((n) => n.ax).strength(0.09);
  fY = forceY<GNode>((n) => n.ay).strength(0.09);
  sim = forceSimulation<GNode, Link>(N)
    .alpha(0.35).alphaDecay(0.035).velocityDecay(0.45)
    .force('x', fX)
    .force('y', fY)
    .force('link', forceLink<GNode, Link>(links()).distance((l) => l.d).strength((l) => l.w))
    .force('collide', forceCollide<GNode>(collideRadius).strength(0.7).iterations(1))
    .stop();
  if (display.physics) kick();
}

function frame(): void {
  raf = 0;
  if (!sim || !display.physics) return;
  sim.tick();
  emit('view');
  if (sim.alpha() > sim.alphaMin() || sim.alphaTarget() > 0) raf = requestAnimationFrame(frame);
}

/** Garante o laço de simulação rodando (opcionalmente reaquecendo). */
function kick(alpha?: number): void {
  if (!sim || !display.physics) return;
  if (alpha !== undefined) sim.alpha(Math.max(sim.alpha(), alpha));
  if (!raf) raf = requestAnimationFrame(frame);
}

export function setPhysics(onOff: boolean): void {
  display.physics = onOff;
  if (onOff) kick(0.3);
  else { cancelAnimationFrame(raf); raf = 0; N.forEach((n) => { n.vx = 0; n.vy = 0; }); }
  emit('view');
}

// ---- Arrastar nós ----
// Os "satélites" de um nó (vizinhos de grau 1, como os orientandos externos em leque) acompanham o
// arraste rigidamente; os demais vizinhos são puxados pelas arestas e voltam ao repouso ao soltar.
let sats: number[] = [];
export function dragStart(i: number): void {
  const n = N[i]!;
  sats = n.adj.map((j) => (E[j]!.a === i ? E[j]!.b : E[j]!.a)).filter((o) => N[o]!.deg === 1);
  if (sim && display.physics) { n.fx = n.x; n.fy = n.y; sim.alphaTarget(0.25); kick(0.25); }
}
export function dragMove(i: number, x: number, y: number): void {
  const n = N[i]!;
  const dx = x - n.ax, dy = y - n.ay;
  n.ax = x; n.ay = y;
  for (const o of sats) {
    const m = N[o]!;
    m.ax += dx; m.ay += dy; m.x += dx; m.y += dy; m.vx = 0; m.vy = 0;
  }
  if (sim && display.physics) { n.fx = x; n.fy = y; refreshAnchors(); kick(); }
  else { n.x = x; n.y = y; n.vx = 0; n.vy = 0; }
  emit('view');
}
export function dragEnd(i: number): void {
  const n = N[i]!;
  sats = [];
  if (sim && display.physics) { n.fx = null; n.fy = null; sim.alphaTarget(0); refreshAnchors(); }
}

// ---- Troca de layout: transição animada das posições ----
let tween = 0;
export function transitionLayout(m: LayoutMode, ms = 650): void {
  cancelAnimationFrame(tween);
  N.forEach((n) => { [n.ax, n.ay] = n.lay[m]; n.vx = 0; n.vy = 0; });
  collideScale = 2.6 * (extent(m) / extentFree);
  if (sim) {
    refreshAnchors();
    (sim.force('link') as ReturnType<typeof forceLink<GNode, Link>>).links(links());
    (sim.force('collide') as ReturnType<typeof forceCollide<GNode>>).radius(collideRadius);
  }
  const from = N.map((n) => [n.x, n.y] as const);
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  const t0 = performance.now();
  const step = (t: number): void => {
    const p = reduced ? 1 : Math.min(1, (t - t0) / ms), e = p < 0.5 ? 4 * p ** 3 : 1 - (-2 * p + 2) ** 3 / 2;
    N.forEach((n, i) => { const f = from[i]!; n.x = f[0] + (n.ax - f[0]) * e; n.y = f[1] + (n.ay - f[1]) * e; });
    emit('view');
    if (p < 1) tween = requestAnimationFrame(step);
    else kick(0.2);
  };
  tween = requestAnimationFrame(step);
}
