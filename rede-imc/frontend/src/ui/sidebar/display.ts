// seções "Cores e layout" e "Exibição"
import { $ } from '../../core/dom';
import { display, emit, emitSoon, filters, on } from '../../core/state';
import type { ColorMode, LayoutMode } from '../../core/types';
import { fitView } from '../../graph/interaction/camera';
import { transitionLayout } from '../../graph/physics';
import { wrapSlider } from './sliders';

const each = <T extends HTMLElement>(sel: string, fn: (el: T) => void): void => document.querySelectorAll<T>(sel).forEach(fn);

export function initDisplay(): void {
  each<HTMLInputElement>('input[name=cm]', (r) => {
    r.addEventListener('change', () => { display.colorMode = r.value as ColorMode; emit('view'); });
  });
  each<HTMLInputElement>('input[name=lm]', (r) => {
    r.addEventListener('change', () => {
      const m = r.value as LayoutMode;
      display.layoutMode = m;
      transitionLayout(m);
      fitView(650, true);
    });
  });

  // só redesenha
  const labImc = $<HTMLInputElement>('labImc');
  labImc.addEventListener('change', () => { display.labelsImc = labImc.checked; emit('view'); });

  const ext = $<HTMLInputElement>('ext'), ms = $<HTMLInputElement>('ms');
  ext.addEventListener('change', () => { filters.showExternal = ext.checked; emit('filters'); });
  const paintMs = wrapSlider(ms);
  ms.addEventListener('input', () => {
    filters.minActivities = Number(ms.value); $('mv').textContent = String(filters.minActivities); emitSoon('filters');
  });

  // sincroniza depois de limpar os filtros
  on('filters', () => {
    ext.checked = filters.showExternal;
    if (Number(ms.value) !== filters.minActivities) {
      ms.value = String(filters.minActivities); $('mv').textContent = String(filters.minActivities); paintMs();
    }
  });
}
