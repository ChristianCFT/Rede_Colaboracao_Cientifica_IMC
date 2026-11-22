// Seções retráteis da sidebar. O estado inicial vem do HTML (data-open) e a escolha do usuário
// é lembrada neste navegador.
import { lsGet, lsSet } from '../../core/dom';

export function initAccordions(): void {
  document.querySelectorAll<HTMLElement>('section.acc').forEach((sec) => {
    const key = sec.dataset['acc'] ?? '';
    const btn = sec.querySelector<HTMLButtonElement>('.acc-t');
    const body = sec.querySelector<HTMLElement>('.acc-b');
    if (!btn || !body) return;
    const saved = lsGet(`imc-rede.acc.${key}`);
    if (saved === '0' || saved === '1') sec.dataset['open'] = saved;
    body.id = body.id || `acc-${key}`;
    btn.setAttribute('aria-controls', body.id);
    const sync = (): void => btn.setAttribute('aria-expanded', String(sec.dataset['open'] === '1'));
    btn.addEventListener('click', () => {
      sec.dataset['open'] = sec.dataset['open'] === '1' ? '0' : '1';
      lsSet(`imc-rede.acc.${key}`, sec.dataset['open']);
      sync();
    });
    sync();
  });
}
