// Controles flutuantes da câmera (canto inferior direito).
import { $ } from '../core/dom';
import { S } from '../core/state';
import { fitView, zoomBy } from '../canvas/camera';
import { setPhysics } from '../canvas/physics';
import { exportPNG } from '../canvas/render';

const svg = (d: string): string => `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="${d}"/></svg>`;
const ICON = {
  plus: svg('M8 3.5v9M3.5 8h9'),
  minus: svg('M3.5 8h9'),
  fit: svg('M2.5 6V2.5H6M10 2.5h3.5V6M13.5 10v3.5H10M6 13.5H2.5V10'),
  pause: svg('M5.5 3.5v9M10.5 3.5v9'),
  play: svg('M5 3.2v9.6L12.6 8z'),
  png: svg('M8 2.5v7.5M4.8 6.8 8 10l3.2-3.2M3 13.5h10'),
};

const btn = (id: string, label: string, icon: string): string =>
  `<button type="button" id="${id}" title="${label}" aria-label="${label}">${icon}</button>`;

export function initCameraControls(): void {
  const el = $('cam');
  el.innerHTML =
    `<div class="glass grp">${btn('zin', 'Aproximar (+)', ICON.plus)}${btn('zout', 'Afastar (−)', ICON.minus)}</div>` +
    `<div class="glass grp">${btn('zfit', 'Ajustar à tela (F)', ICON.fit)}${btn('phy', '', '')}${btn('png', 'Exportar imagem (PNG)', ICON.png)}</div>`;
  $('zin').addEventListener('click', () => zoomBy(1.4));
  $('zout').addEventListener('click', () => zoomBy(1 / 1.4));
  $('zfit').addEventListener('click', () => fitView());
  $('png').addEventListener('click', () => exportPNG());
  const phy = $<HTMLButtonElement>('phy');
  const paint = (): void => {
    const label = S.physics ? 'Pausar física' : 'Retomar física';
    phy.innerHTML = S.physics ? ICON.pause : ICON.play;
    phy.title = label; phy.setAttribute('aria-label', label); phy.setAttribute('aria-pressed', String(!S.physics));
  };
  phy.addEventListener('click', () => { setPhysics(!S.physics); paint(); });
  paint();
}
