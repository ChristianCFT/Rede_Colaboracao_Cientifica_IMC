// Peso normalizado da colaboração (proposta metodológica, seções 4 e 5). Mesma fórmula do backend
// (backend/src/engine/peso.py): para cada dimensão, z = ln(1 + x) / ln(1 + maior valor da rede);
// o peso é a soma de α · z, entre 0 e 1. As referências (maiores valores) vêm da rede inteira e não
// mudam com os filtros: assim o peso de um recorte continua comparável com o de outro.

/** Importância de cada dimensão (art, prj, ori, ban, ptt), somando 1. */
export let ALFA: number[] = [];
/** Maior contagem de cada dimensão na rede inteira. */
export let REF: number[] = [];
/** Maior peso de relação na rede inteira (topo da escala de espessura). */
export let WMAX = 1;
/** Pesos de todas as relações da rede inteira, em ordem crescente (quantis da legenda). */
let ORDENADOS: number[] = [];

export function initPeso(alfas: number[], referencias: number[], pesos: number[]): void {
  ALFA = alfas; REF = referencias;
  ORDENADOS = [...pesos].sort((a, b) => a - b);
  WMAX = ORDENADOS.length ? ORDENADOS[ORDENADOS.length - 1]! : 1;
}

/** Peso de uma relação a partir das contagens por dimensão. Dimensão sem nenhuma atividade na rede vale 0. */
export function pesoDe(contagem: number[]): number {
  let w = 0;
  for (let j = 0; j < contagem.length; j++) {
    if (REF[j]! > 0) w += ALFA[j]! * Math.log1p(contagem[j]!) / Math.log1p(REF[j]!);
  }
  return w;
}

/** Tamanho visual de um peso, de 0 a 1: raiz de W / maior W. A raiz espalha os pesos baixos
 *  (a maioria fica abaixo de 0,10) sem mudar a ordem entre as relações. */
export const escala = (w: number): number => (WMAX > 0 ? Math.sqrt(Math.min(1, w / WMAX)) : 0);

/** Peso no quantil q (0 a 1) entre todas as relações da rede (valores de exemplo da legenda). */
export const quantil = (q: number): number =>
  ORDENADOS.length ? ORDENADOS[Math.min(ORDENADOS.length - 1, Math.floor(q * ORDENADOS.length))]! : 0;
