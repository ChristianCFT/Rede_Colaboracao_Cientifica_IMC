// Seções "Cores e layout" e "Exibição".
import { $ } from '../../core/dom';
import { display, emit, emitSoon, filters, on } from '../../core/state';
import type { ColorMode, LayoutMode } from '../../core/types';
import { fitView } from '../../graph/interaction/camera';
import { transitionLayout } from '../../graph/physics';
import { wrapSlider } from './sliders';

const each = <T extends HTMLElement>(sel: string, fn: (el: T) => void): void => document.querySelectorAll<T>(sel).forEach(fn);

function help(): void {
  const espessura = display.peso
    ? 'Espessura da aresta = peso da colaboração (0 a 1, normalizado pelo maior valor da rede). '
    : 'Espessura da aresta = atividades em comum no recorte (sem normalização). ';
  $('help').textContent = `Cor do nó = ${display.colorMode === 'area' ? 'área do IMC' : 'instituto'}. ` + espessura +
    'Arraste o fundo para mover, arraste um nó para reposicioná-lo, ' +
    'role para dar zoom e clique em um nó ou aresta para ver detalhes. Atalhos: Esc limpa a seleção, + / − zoom, F enquadra, P liga o peso.';
}

export function initDisplay(): void {
  each<HTMLInputElement>('input[name=cm]', (r) => {
    r.addEventListener('change', () => { display.colorMode = r.value as ColorMode; help(); emit('view'); });
  });
  each<HTMLInputElement>('input[name=lm]', (r) => {
    r.addEventListener('change', () => {
      const m = r.value as LayoutMode;
      display.layoutMode = m;
      transitionLayout(m);
      fitView(650, true);
    });
  });

  // Rótulos dos pesquisadores do IMC: só redesenham (não recalculam o recorte).
  const labImc = $<HTMLInputElement>('labImc');
  labImc.addEventListener('change', () => { display.labelsImc = labImc.checked; emit('view'); });

  const ext = $<HTMLInputElement>('ext'), ms = $<HTMLInputElement>('ms');
  ext.addEventListener('change', () => { filters.showExternal = ext.checked; emit('filters'); });
  const paintMs = wrapSlider(ms);
  ms.addEventListener('input', () => {
    filters.minActivities = Number(ms.value); $('mv').textContent = String(filters.minActivities); emitSoon('filters');
  });

  on('peso', help);

  // Sincroniza com o estado (ex.: depois de "Limpar filtros").
  on('filters', () => {
    ext.checked = filters.showExternal;
    if (Number(ms.value) !== filters.minActivities) {
      ms.value = String(filters.minActivities); $('mv').textContent = String(filters.minActivities); paintMs();
    }
  });
  help();
}
