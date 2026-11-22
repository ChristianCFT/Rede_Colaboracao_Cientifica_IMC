// carrega o grafo e inicia os módulos
import { api, ApiError } from './api/api';
import { initModel } from './core/model';
import { initState } from './core/state';
import { fitView } from './graph/interaction/camera';
import { initMouse } from './graph/interaction/mouse';
import { initPhysics } from './graph/physics';
import { initRender, resize } from './graph/render/scene';
import { initCameraControls } from './ui/cameraControls';
import { initDetails } from './ui/details';
import { initHUD } from './ui/hud';
import { initPesoToggle } from './ui/pesoToggle';
import { initSidebar } from './ui/sidebar';

const boot = document.createElement('div');
boot.className = 'boot';
document.body.appendChild(boot);

function setBoot(html: string, retry = false): void {
  boot.innerHTML = `<div class="boot-box">${html}${retry ? '<p><button id="retry">Tentar novamente</button></p>' : ''}</div>`;
  if (retry) document.getElementById('retry')?.addEventListener('click', () => void start());
}

async function start(): Promise<void> {
  setBoot('<b>Carregando a rede de colaboração…</b><p class="mu">Na primeira requisição o backend calcula os layouts.</p>');
  try {
    initModel(await api.graph());
  } catch (e) {
    setBoot(`<b>Não foi possível carregar o grafo.</b><p class="mu">${e instanceof ApiError ? e.message : 'Erro inesperado.'}</p>`, true);
    return;
  }
  initState();
  initRender();
  initSidebar();
  initHUD();
  initCameraControls();
  initPesoToggle();
  initDetails();
  initMouse();
  boot.remove();
  resize();
  fitView(0);
  initPhysics();
}
void start();
