// Intermediação (betweenness) exata — algoritmo de Brandes para grafo não direcionado e sem pesos.
// Função pura: recebe o número de nós e as arestas em índices locais (0..n-1) e devolve a
// intermediação normalizada como no NetworkX (2 / ((n-1)(n-2)) após dividir por 2).
export function brandes(n: number, ea: Int32Array, eb: Int32Array): Float64Array {
  const off = new Int32Array(n + 1);
  for (let j = 0; j < ea.length; j++) { off[ea[j]! + 1]!++; off[eb[j]! + 1]!++; }
  for (let i = 0; i < n; i++) off[i + 1]! += off[i]!;
  const nb = new Int32Array(off[n]!), fill = off.slice(0, n);
  for (let j = 0; j < ea.length; j++) { const a = ea[j]!, b = eb[j]!; nb[fill[a]!++] = b; nb[fill[b]!++] = a; }
  const cb = new Float64Array(n), sigma = new Float64Array(n), delta = new Float64Array(n);
  const dist = new Int32Array(n).fill(-1), order = new Int32Array(n);
  for (let s = 0; s < n; s++) {
    let head = 0, tail = 0;
    order[tail++] = s; dist[s] = 0; sigma[s] = 1;
    while (head < tail) {
      const w = order[head++]!;
      for (let p = off[w]!; p < off[w + 1]!; p++) {
        const u = nb[p]!;
        if (dist[u]! < 0) { dist[u] = dist[w]! + 1; order[tail++] = u; }
        if (dist[u] === dist[w]! + 1) sigma[u]! += sigma[w]!;
      }
    }
    for (let q = tail - 1; q >= 0; q--) {
      const w = order[q]!;
      for (let p = off[w]!; p < off[w + 1]!; p++) {
        const u = nb[p]!;
        if (dist[u] === dist[w]! - 1) delta[u]! += (sigma[u]! / sigma[w]!) * (1 + delta[w]!);
      }
      if (w !== s) cb[w]! += delta[w]!;
    }
    for (let q = 0; q < tail; q++) { const w = order[q]!; dist[w] = -1; sigma[w] = 0; delta[w] = 0; }
  }
  const norm = n > 2 ? 1 / ((n - 1) * (n - 2)) : 0;
  for (let i = 0; i < n; i++) cb[i]! *= norm;
  return cb;
}
