// Ponto de entrada: carrega o grafo da API (com loading/erro) e orquestra os módulos.
//
//   core/      modelo, estado + eventos, seletores memoizados, ações de seleção
//   canvas/    render (holofote + rótulos), câmera, física, interação
//   ui/        sidebar/ (filtros), hud (KPIs), cameraControls, details/ (painel direito)
import { api, ApiError } from './services/api';
import { initModel } from './core/model';
import { initState } from './core/state';
import { primeScales } from './core/selectors';
import { initRender, resize } from './canvas/render';
import { initPhysics } from './canvas/physics';
import { initInteraction } from './canvas/interaction';
import { fitView } from './canvas/camera';
import { initSidebar } from './ui/sidebar';
import { initHUD } from './ui/hud';
import { initCameraControls } from './ui/cameraControls';
import { initDetails } from './ui/details';

const boot = document.createElement('div');
boot.style.cssText = 'position:fixed;inset:0;z-index:9;display:grid;place-items:center;background:var(--bg);color:var(--tx);font:13px system-ui,sans-serif;text-align:center';
document.body.appendChild(boot);

function setBoot(html: string, retry = false): void {
  boot.innerHTML = `<div style="max-width:380px;padding:20px">${html}${retry ? '<p><button id="retry">Tentar novamente</button></p>' : ''}</div>`;
  if (retry) document.getElementById('retry')?.addEventListener('click', () => void start());
}

async function start(): Promise<void> {
  setBoot('<b>Carregando a rede de colaboração…</b><p style="color:var(--mu)">Na primeira requisição o backend calcula os layouts e métricas.</p>');
  try {
    initModel(await api.graph());
  } catch (e) {
    setBoot(`<b>Não foi possível carregar o grafo.</b><p style="color:var(--mu)">${e instanceof ApiError ? e.message : 'Erro inesperado.'}</p>`, true);
    return;
  }
  initState();
  primeScales();
  initRender();
  initSidebar();
  initHUD();
  initCameraControls();
  initDetails();
  initInteraction();
  boot.remove();
  resize();
  fitView(0);
  initPhysics();
}
void start();
