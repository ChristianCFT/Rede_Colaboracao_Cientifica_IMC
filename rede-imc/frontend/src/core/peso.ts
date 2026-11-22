// mesma fórmula do backend/src/engine/peso.py. as referências são da rede inteira,
// não mudam com os filtros

export let ALFA: number[] = [];
export let REF: number[] = [];
/** usado na escala de espessura */
export let WMAX = 1;
/** ordenado, usado na legenda */
let ORDENADOS: number[] = [];

export function initPeso(alfas: number[], referencias: number[], pesos: number[]): void {
  ALFA = alfas; REF = referencias;
  ORDENADOS = [...pesos].sort((a, b) => a - b);
  WMAX = ORDENADOS.length ? ORDENADOS[ORDENADOS.length - 1]! : 1;
}

export function pesoDe(contagem: number[]): number {
  let w = 0;
  for (let j = 0; j < contagem.length; j++) {
    if (REF[j]! > 0) w += ALFA[j]! * Math.log1p(contagem[j]!) / Math.log1p(REF[j]!);
  }
  return w;
}

/** W / maior W da rede */
export const escala = (w: number): number => (WMAX > 0 ? Math.min(1, w / WMAX) : 0);

/** usado na legenda */
export const quantil = (q: number): number =>
  ORDENADOS.length ? ORDENADOS[Math.min(ORDENADOS.length - 1, Math.floor(q * ORDENADOS.length))]! : 0;
