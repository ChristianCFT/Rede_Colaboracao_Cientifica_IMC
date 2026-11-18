// Utilitários de DOM e formatação (pt-BR).

export const $ = <T extends HTMLElement = HTMLElement>(id: string): T => {
  const e = document.getElementById(id);
  if (!e) throw new Error(`Elemento #${id} ausente no index.html`);
  return e as T;
};

const ENT: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };
export const esc = (s: unknown): string => String(s).replace(/[&<>"]/g, (c) => ENT[c] ?? c);

const nf0 = new Intl.NumberFormat('pt-BR');
const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
/** 1486 → "1.486" */
export const fmt = (n: number): string => nf0.format(n);
/** 3.806 → "3,8" */
export const fmt1 = (n: number): string => nf1.format(n);
/** 0.684 → "68%" (com uma casa abaixo de 10%). */
export const pct = (x: number): string => (x > 0 && x < 0.1 ? `${fmt1(x * 100)}%` : `${Math.round(x * 100)}%`);

export const lsGet = (k: string): string | null => { try { return localStorage.getItem(k); } catch { return null; } };
export const lsSet = (k: string, v: string): void => { try { localStorage.setItem(k, v); } catch { /* armazenamento indisponível */ } };
