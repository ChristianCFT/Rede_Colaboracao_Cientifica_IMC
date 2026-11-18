// Seções "Cores e layout" e "Exibição".
import { $ } from '../../core/dom';
import { S, emit, emitSoon, on } from '../../core/state';
import { fitView } from '../../canvas/camera';
import { transitionLayout } from '../../canvas/physics';
import type { ColorMode, LayoutMode, SizeMetric } from '../../types/graph';
import { wrapSlider } from './sliders';

const each = <T extends HTMLElement>(sel: string, fn: (el: T) => void): void => document.querySelectorAll<T>(sel).forEach(fn);

const SIZE_TXT: Record<SizeMetric, string> = {
  deg: 'grau (nº de parceiros no recorte)',
  vol: 'volume de produções (atividades distintas no recorte)',
  btw: 'intermediação (betweenness) no recorte',
};

function help(): void {
  $('help').textContent = `Cor do nó = ${S.colorMode === 'area' ? 'área do IMC' : 'instituto'}. Tamanho do nó = ${SIZE_TXT[S.sizeMetric]}. ` +
    'Espessura da aresta = atividades em comum no recorte (sem normalização). Arraste o fundo para mover, arraste um nó para reposicioná-lo, ' +
    'role para dar zoom e clique em um nó ou aresta para ver detalhes. Atalhos: Esc limpa a seleção, + / − zoom, F enquadra.';
}

export function initDisplay(): void {
  each<HTMLInputElement>('input[name=cm]', (r) => { r.addEventListener('change', () => { S.colorMode = r.value as ColorMode; help(); emit('view'); }); });
  each<HTMLInputElement>('input[name=lm]', (r) => {
    r.addEventListener('change', () => {
      const m = r.value as LayoutMode;
      S.layoutMode = m;
      transitionLayout(m);
      fitView(650, true);
    });
  });
  each<HTMLInputElement>('input[name=sz]', (r) => { r.addEventListener('change', () => { S.sizeMetric = r.value as SizeMetric; help(); emit('view'); }); });

  const lab = $<HTMLInputElement>('lab'), ext = $<HTMLInputElement>('ext'), ms = $<HTMLInputElement>('ms');
  lab.addEventListener('change', () => { S.showLab = lab.checked; emit('view'); });
  ext.addEventListener('change', () => { S.showExt = ext.checked; emit('filters'); });
  const paintMs = wrapSlider(ms);
  ms.addEventListener('input', () => { S.minS = Number(ms.value); $('mv').textContent = String(S.minS); emitSoon('filters'); });

  // Sincroniza com o estado (ex.: depois de "Limpar filtros").
  on('filters', () => {
    ext.checked = S.showExt;
    if (Number(ms.value) !== S.minS) { ms.value = String(S.minS); $('mv').textContent = String(S.minS); paintMs(); }
  });
  help();
}
