import { useEffect, useRef } from "react";

const WS_BASE = import.meta.env.VITE_WS_BASE;

// Opens a WS connection authenticated by token, calls onEvent for each message.
export function useLiveUpdates(token, onEvent) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!token) return;
    const ws = new WebSocket(`${WS_BASE}/ws?token=${token}`);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "unit_changed") onEventRef.current(data);
      } catch {
        /* ignore malformed */
      }
    };
    ws.onclose = (e) => {
      if (e.code === 4401) console.warn("WS auth rejected");
    };

    return () => ws.close();
  }, [token]);
}