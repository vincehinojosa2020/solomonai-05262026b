import { useEffect, useRef } from 'react';

/**
 * usePolling — calls `callback` every `intervalMs` while the tab is visible.
 * Pauses automatically when the browser tab is hidden (saves resources).
 *
 * @param {Function} callback  — async or sync function to invoke
 * @param {number}   intervalMs — polling interval in milliseconds (default 30000)
 * @param {boolean}  enabled   — toggle polling on/off (default true)
 */
export function usePolling(callback, intervalMs = 30000, enabled = true) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;

    let id;

    const tick = () => {
      try { savedCallback.current(); } catch (_) { /* swallow */ }
    };

    const start = () => { id = setInterval(tick, intervalMs); };
    const stop  = () => { clearInterval(id); };

    const onVisibility = () => {
      if (document.hidden) { stop(); } else { start(); tick(); }
    };

    start();
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      stop();
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [intervalMs, enabled]);
}
