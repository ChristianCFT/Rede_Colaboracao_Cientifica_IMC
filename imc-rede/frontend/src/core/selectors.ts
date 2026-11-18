// Seletores memoizados: o recorte filtrado (nós, arestas, pesos por dimensão), os contadores das
// facetas, os KPIs do HUD e as métricas de tamanho. Equivalente ao useMemo do React: cada resultado
// é guardado junto com a chave de que depende (versão dos filtros + centro do ego) e só é recalculado
// quando ela muda. Hover, câmera e física não invalidam nada.
import { CODE_DIM, CODE_YEAR, E, MAX_DEG, N, NCODES } from './model';
import { S, dimOn, emit, filterVer, grpOn, imcVis, typeOn, yearFull } from './state';
import { brandes } from './betweenness';

/** Recorte base: todos os filtros da sidebar aplicados (sem o modo ego). */
export interface Cut {
  ver: number;
  /** Atividade passa na janela temporal (independe das dimensões). */
  inWin: Uint8Array;
  /** Atividade passa na janela temporal E na sua dimensão estar ativa. */
  ok: Uint8Array;
  /** Contagem filtrada por aresta e dimensão: fvc[e*5 + j]. */
  fvc: Int32Array;
  /** Soma filtrada por aresta (peso usado em espessura, ordenação e "mín. de atividades"). */
  fsum: Int32Array;
  eOn: Uint8Array;
  nOn: Uint8Array;
  /** Contadores das facetas (cada faceta ignora o próprio filtro, como numa busca facetada). */
  facets: { types: Record<string, number>; grps: Record<string, number>; dims: number[]; win: number };
}

/** Recorte visível: o base + o modo ego (1º e 2º graus) quando ativo. */
export interface View {
  key: string;
  cut: Cut;
  eOn: Uint8Array;
  nOn: Uint8Array;
  nE: number;
  nN: number;
  /** Nº de parceiros visíveis por nó. */
  deg: Int32Array;
  /** Atividades distintas visíveis por nó. */
  vol: Int32Array;
  /** Atividades distintas visíveis por dimensão. */
  dimAct: number[];
  totAct: number;
  avgDeg: number;
  ego: { center: number; size: number } | null;
}

const grpsOf = (i: number): string[] => {
  const n = N[i]!;
  if (n.inst !== 'IMC') return [];
  const g: string[] = [];
  if (n.comp) g.push('Computação');
  if (n.mat) g.push('Matemática');
  if (!n.comp && !n.mat) g.push('Outras');
  return g;
};

let cutMemo: Cut | null = null;
export function getCut(): Cut {
  const ver = filterVer();
  if (cutMemo && cutMemo.ver === ver) return cutMemo;

  const full = yearFull();
  const inWin = new Uint8Array(NCODES), ok = new Uint8Array(NCODES);
  for (let c = 0; c < NCODES; c++) {
    const y = CODE_YEAR[c]!;
    const w = full || (y > 0 && y >= S.y0 && y <= S.y1);
    inWin[c] = w ? 1 : 0;
    ok[c] = w && dimOn[CODE_DIM[c]!] ? 1 : 0;
  }

  const m = E.length;
  const fvc = new Int32Array(m * 5), fsum = new Int32Array(m), eOn = new Uint8Array(m);
  const types: Record<string, number> = {};
  Object.keys(typeOn).forEach((t) => { types[t] = 0; });
  const grpMark = new Uint8Array(N.length);
  const dimStamp = new Uint8Array(NCODES);
  const dims = [0, 0, 0, 0, 0];
  const winStamp = new Uint8Array(NCODES);
  let win = 0;

  for (let e = 0; e < m; e++) {
    const ed = E[e]!, a = N[ed.a]!, b = N[ed.b]!;
    let s = 0;
    for (let j = 0; j < 5; j++) {
      if (!dimOn[j]) continue;
      let c = 0;
      for (const k of ed.cd[j]!) c += ok[k]!;
      fvc[e * 5 + j] = c; s += c;
    }
    fsum[e] = s;
    const pT = !!typeOn[ed.tipo];
    const pA = imcVis(a) && imcVis(b);
    const pX = S.showExt || (a.inst !== 'EXT' && b.inst !== 'EXT');
    const pW = s > 0 && s >= S.minS;
    if (pT && pA && pX && pW) eOn[e] = 1;
    if (pA && pX && pW) types[ed.tipo] = (types[ed.tipo] ?? 0) + 1;
    if (pT && pX && pW) { grpMark[ed.a] = 1; grpMark[ed.b] = 1; }
    if (pT && pA && pX) {
      for (let j = 0; j < 5; j++) {
        for (const k of ed.cd[j]!) {
          if (!inWin[k]) continue;
          if (!dimStamp[k]) { dimStamp[k] = 1; dims[j]!++; }
          if (!winStamp[k]) { winStamp[k] = 1; win++; }
        }
      }
    }
  }

  const grps: Record<string, number> = {};
  Object.keys(grpOn).forEach((g) => { grps[g] = 0; });
  grpMark.forEach((v, i) => { if (v) grpsOf(i).forEach((g) => { grps[g] = (grps[g] ?? 0) + 1; }); });

  const nOn = new Uint8Array(N.length);
  for (let i = 0; i < N.length; i++) {
    const n = N[i]!;
    if (n.inst === 'IMC') nOn[i] = imcVis(n) ? 1 : 0;
    else if (n.inst === 'EXT' && !S.showExt) nOn[i] = 0;
    else nOn[i] = n.adj.some((j) => eOn[j] === 1) ? 1 : 0;
  }

  cutMemo = { ver, inWin, ok, fvc, fsum, eOn, nOn, facets: { types, grps, dims, win } };
  return cutMemo;
}

let viewMemo: View | null = null;
export function getView(): View {
  const cut = getCut();
  const center = S.ego && S.sel >= 0 && cut.nOn[S.sel] ? S.sel : -1;
  const key = `${cut.ver}|${center}`;
  if (viewMemo && viewMemo.key === key) return viewMemo;

  let eOn = cut.eOn, nOn = cut.nOn;
  let ego: View['ego'] = null;
  if (center >= 0) {
    // BFS de profundidade 2 sobre as arestas do recorte base.
    const dist = new Int8Array(N.length).fill(-1);
    dist[center] = 0;
    let frontier = [center];
    for (let d = 1; d <= 2; d++) {
      const next: number[] = [];
      for (const u of frontier) {
        for (const j of N[u]!.adj) {
          if (!cut.eOn[j]) continue;
          const ed = E[j]!, v = ed.a === u ? ed.b : ed.a;
          if (dist[v] === -1) { dist[v] = d; next.push(v); }
        }
      }
      frontier = next;
    }
    nOn = new Uint8Array(N.length);
    let size = 0;
    dist.forEach((d, i) => { if (d >= 0) { nOn[i] = 1; size++; } });
    eOn = new Uint8Array(E.length);
    for (let j = 0; j < E.length; j++) if (cut.eOn[j] && nOn[E[j]!.a] && nOn[E[j]!.b]) eOn[j] = 1;
    ego = { center, size };
  }

  const deg = new Int32Array(N.length);
  let nE = 0;
  for (let j = 0; j < E.length; j++) if (eOn[j]) { nE++; deg[E[j]!.a]!++; deg[E[j]!.b]!++; }
  let nN = 0;
  for (let i = 0; i < N.length; i++) nN += nOn[i]!;

  // Atividades distintas por nó e por dimensão (marcação com "carimbo" para evitar Sets).
  const vol = new Int32Array(N.length);
  const stamp = new Int32Array(NCODES).fill(-1);
  for (let i = 0; i < N.length; i++) {
    if (!nOn[i]) continue;
    let c = 0;
    for (const j of N[i]!.adj) {
      if (!eOn[j]) continue;
      for (const arr of E[j]!.cd) for (const k of arr) if (cut.ok[k] && stamp[k] !== i) { stamp[k] = i; c++; }
    }
    vol[i] = c;
  }
  const dimAct = [0, 0, 0, 0, 0];
  const seen = new Uint8Array(NCODES);
  for (let j = 0; j < E.length; j++) {
    if (!eOn[j]) continue;
    E[j]!.cd.forEach((arr, d) => { for (const k of arr) if (cut.ok[k] && !seen[k]) { seen[k] = 1; dimAct[d]!++; } });
  }
  const totAct = dimAct.reduce((s, x) => s + x, 0);

  viewMemo = { key, cut, eOn, nOn, nE, nN, deg, vol, dimAct, totAct, avgDeg: nN ? (2 * nE) / nN : 0, ego };
  return viewMemo;
}

/** Atividades distintas de um nó, por dimensão, dentro do recorte visível. */
export function nodeDims(i: number, v: View = getView()): number[] {
  const out = [0, 0, 0, 0, 0];
  const seen = new Set<number>();
  for (const j of N[i]!.adj) {
    if (!v.eOn[j]) continue;
    E[j]!.cd.forEach((arr, d) => { for (const k of arr) if (v.cut.ok[k] && !seen.has(k)) { seen.add(k); out[d]!++; } });
  }
  return out;
}

// ---- Intermediação (betweenness) exata no recorte visível ----
// Calculada sob demanda num Web Worker (ou na thread principal, se Worker não existir). Enquanto o
// resultado do recorte atual não chega, devolvemos o último disponível (marcado como não "fresh").
let btwMemo: { key: string; val: Float64Array; max: number } | null = null;
let btwPending = '';
let btwTimer = 0;
let worker: Worker | null | undefined;
let workerNodes: number[] = [];

function finishBtw(key: string, nodes: number[], local: Float64Array): void {
  const val = new Float64Array(N.length);
  let max = 0;
  nodes.forEach((g, l) => { val[g] = local[l]!; if (local[l]! > max) max = local[l]!; });
  btwMemo = { key, val, max };
  if (btwPending === key) btwPending = '';
  emit('view');
}

function requestBtw(v: View): void {
  const nodes: number[] = [];
  const loc = new Int32Array(N.length).fill(-1);
  for (let i = 0; i < N.length; i++) if (v.nOn[i]) { loc[i] = nodes.length; nodes.push(i); }
  const ea = new Int32Array(v.nE), eb = new Int32Array(v.nE);
  let k = 0;
  for (let j = 0; j < E.length; j++) if (v.eOn[j]) { ea[k] = loc[E[j]!.a]!; eb[k] = loc[E[j]!.b]!; k++; }
  if (worker === undefined) {
    try {
      worker = new Worker(new URL('./betweenness.worker.ts', import.meta.url), { type: 'module' });
      worker.onmessage = (ev: MessageEvent<{ key: string; val: Float64Array }>) => {
        if (ev.data.key === btwPending) finishBtw(ev.data.key, workerNodes, ev.data.val);
      };
    } catch { worker = null; }
  }
  if (worker) {
    workerNodes = nodes;
    worker.postMessage({ key: v.key, n: nodes.length, ea, eb }, [ea.buffer, eb.buffer]);
  } else {
    finishBtw(v.key, nodes, brandes(nodes.length, ea, eb));
  }
}

/** Intermediação do recorte atual; null enquanto o primeiro cálculo não terminou. */
export function getBetweenness(): { val: Float64Array; max: number; fresh: boolean } | null {
  const v = getView();
  if (btwMemo && btwMemo.key === v.key) return { ...btwMemo, fresh: true };
  if (btwPending !== v.key) {
    btwPending = v.key;
    window.clearTimeout(btwTimer);
    btwTimer = window.setTimeout(() => { if (btwPending === v.key) requestBtw(getView()); }, btwMemo ? 120 : 0);
  }
  return btwMemo ? { ...btwMemo, fresh: false } : null;
}

// ---- Tamanho dos nós ----
// Grau e volume usam escala absoluta (mesma fórmula do projeto original: 2,5 + 1,8·√grau), então o
// tamanho continua comparável quando o filtro muda. A intermediação é relativa ao maior valor do recorte.
let volScale = 0;
let radMemo: { key: string; r: Float32Array } | null = null;

export function baseRadii(): Float32Array {
  const v = getView();
  let key = `${v.key}|${S.sizeMetric}`;
  let btw: ReturnType<typeof getBetweenness> = null;
  if (S.sizeMetric === 'btw') { btw = getBetweenness(); key += `|${btw ? btw.max : 'na'}`; }
  if (radMemo && radMemo.key === key) return radMemo.r;

  const r = new Float32Array(N.length);
  const R = 1.8 * Math.sqrt(MAX_DEG);
  if (S.sizeMetric === 'vol') {
    if (!volScale) {
      // Escala fixada na rede completa: o maior volume recebe o mesmo raio do maior grau.
      let mv = 1;
      v.vol.forEach((x) => { if (x > mv) mv = x; });
      volScale = Math.sqrt(MAX_DEG / mv);
    }
    for (let i = 0; i < N.length; i++) r[i] = 2.5 + 1.8 * Math.sqrt(v.vol[i]!) * volScale;
  } else if (S.sizeMetric === 'btw' && btw && btw.max > 0) {
    for (let i = 0; i < N.length; i++) r[i] = 2.5 + R * Math.sqrt(btw.val[i]! / btw.max);
  } else {
    for (let i = 0; i < N.length; i++) r[i] = 2.5 + 1.8 * Math.sqrt(v.deg[i]!);
  }
  radMemo = { key, r };
  return r;
}

/** Fixa a escala do volume na rede completa (chamado uma vez, antes de qualquer filtro). */
export function primeScales(): void {
  const v = getView();
  let mv = 1;
  v.vol.forEach((x) => { if (x > mv) mv = x; });
  volScale = Math.sqrt(MAX_DEG / mv);
}
