// interruptor do peso e legenda (atalho: P)
import { $, fmtPeso } from '../core/dom';
import { WMAX, escala, quantil } from '../core/peso';
import { display, on, setPeso } from '../core/state';
import { espessura, opacidade } from '../graph/render/edges';

// ícone de tomada
const TOMADA = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 1.5v3M10 1.5v3M4 4.5h8v3a4 4 0 0 1-8 0zM8 11.5v3"/></svg>';

const amostra = (w: number, texto: string): string =>
  `<svg viewBox="0 0 36 10" aria-hidden="true"><line x1="3" y1="5" x2="33" y2="5" stroke-width="${espessura(escala(w)).toFixed(2)}"` +
  ` stroke-opacity="${opacidade(escala(w)).toFixed(2)}"/></svg>` +
  `<b class="num">${fmtPeso(w)}</b><span class="mu">${texto}</span>`;

export function initPesoToggle(): void {
  const el = $('peso');
  el.innerHTML =
    `<button type="button" role="switch" class="chave" title="Ligar ou desligar o peso da colaboração (tecla P)">${TOMADA}` +
    '<span>Peso da colaboração</span><span class="trilho"><span class="pino"></span></span></button>' +
    '<div class="legenda"><div class="mu">Espessura e intensidade da aresta = peso (0 a 1)</div>' +
    `<div class="amostras">${amostra(quantil(0.5), 'metade das relações')}${amostra(quantil(0.9), '10% mais fortes')}${amostra(WMAX, 'maior da rede')}</div></div>`;
  const chave = el.querySelector<HTMLButtonElement>('.chave')!;
  chave.addEventListener('click', () => setPeso(!display.peso));
  const paint = (): void => {
    chave.setAttribute('aria-checked', String(display.peso));
    el.classList.toggle('ligado', display.peso);
  };
  on('peso', paint);
  paint();
}
