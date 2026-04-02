import { useEffect, useRef, useCallback, useState } from 'react';

const WS_RECONNECT_DELAY = 3000;
const WS_PING_INTERVAL = 30000;

export function useWebSocket(onMessage, { enabled = true } = {}) {
  const wsRef = useRef(null);
  const pingRef = useRef(null);
  const reconnectRef = useRef(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (!enabled) return;
    const userData = JSON.parse(sessionStorage.getItem('user_data') || '{}');
    const tenantId = userData.tenant_id;
    const userId = userData.user_id;
    if (!tenantId || !userId) return;

    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    const wsUrl = backendUrl.replace(/^http/, 'ws') + `/ws/${tenantId}/${userId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Start ping keepalive
        pingRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, WS_PING_INTERVAL);
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const msg = JSON.parse(event.data);
          onMessage?.(msg);
        } catch {}
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval(pingRef.current);
        // Auto reconnect
        reconnectRef.current = setTimeout(connect, WS_RECONNECT_DELAY);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available, polling will be used as fallback
      setConnected(false);
    }
  }, [enabled, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      clearInterval(pingRef.current);
      clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on cleanup
        wsRef.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return { connected, send };
}
