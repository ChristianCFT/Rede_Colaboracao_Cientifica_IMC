// Web Worker: calcula a intermediação fora da thread principal (sem travar a interface).
import { brandes } from './betweenness';

interface Req { key: string; n: number; ea: Int32Array; eb: Int32Array }
self.onmessage = (ev: MessageEvent<Req>): void => {
  const { key, n, ea, eb } = ev.data;
  const val = brandes(n, ea, eb);
  (self as unknown as Worker).postMessage({ key, val }, [val.buffer]);
};
