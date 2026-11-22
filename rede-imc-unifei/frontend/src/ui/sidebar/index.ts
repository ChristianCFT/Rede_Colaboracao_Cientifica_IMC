// Barra lateral esquerda: monta as seções na ordem do HTML.
import { initAccordions } from './accordion';
import { initDisplay } from './display';
import { initFacets } from './facets';
import { initFilterSummary } from './filterSummary';
import { initNetwork } from './network';
import { initSearch } from './search';
import { initTimeWindow } from './sliders';

export function initSidebar(): void {
  initAccordions();
  initSearch();
  initFacets();
  initTimeWindow();
  initNetwork();
  initDisplay();
  initFilterSummary();
}
