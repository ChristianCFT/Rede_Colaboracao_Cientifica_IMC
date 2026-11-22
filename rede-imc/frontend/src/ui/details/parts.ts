import { esc, fmt, pct } from '../../core/dom';
import { DIMN, N, col } from '../../core/model';

export const vec = (v: number[]): string =>
  `<div class="vec">${v.map((x, j) => `<div><b>${fmt(x)}</b><span>${esc(DIMN[j] ?? '')}</span></div>`).join('')}</div>`;

export const nameLink = (i: number): string => `<a href="#" class="nl" data-n="${i}"><b>${esc(N[i]!.name)}</b></a>`;

export const dot = (color: string): string => `<span class="sw" style="background:${color}"></span>`;

export interface BarRow { label: string; title?: string; color: string; value: number; frac: number; muted?: boolean }
/** ex: "40% · 12" */
export function bars(rows: BarRow[]): string {
  return `<div class="bars">${rows.map((r) => {
    const w = Math.max(0, Math.min(1, r.frac)) * 100;
    return `<span class="bl${r.muted ? ' muted' : ''}"${r.title ? ` title="${esc(r.title)}"` : ''}>${dot(r.color)}${esc(r.label)}</span>` +
      `<span class="bt"><span class="bf" style="width:${w.toFixed(2)}%;background:${r.color}"></span></span>` +
      `<span class="bv">${r.muted ? '—' : `<b>${pct(r.frac)}</b> · ${fmt(r.value)}`}</span>`;
  }).join('')}</div>`;
}

export function personRow(rank: number, i: number, right: string): string {
  const n = N[i]!;
  return `<div class="pr" data-n="${i}"><span class="rk">${rank}</span>${dot(col(n.inst))}` +
    `<span class="nm">${esc(n.name)} <span class="mu">· ${esc(n.inst)}</span></span>${right}</div>`;
}
