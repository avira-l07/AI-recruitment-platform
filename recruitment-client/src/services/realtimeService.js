const realtimeService = {
  /**
   * Connects to the server-sent events stream at /analytics/events/stream.
   * Enforces credentials, parses chunks line-by-line, and recovers using exponential backoff.
   */
  connectEventStream: (token, lastEventId, onEvent, onError, onStatusChange) => {
    let active = true;
    let reader = null;
    let reconnectTimeout = null;
    let resolveReconnect = null;
    let controller = null;
    let delay = 1000;
    const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

    const runStream = async () => {
      while (active) {
        try {
          const url = `${API_BASE_URL.replace(/\/$/, '')}/analytics/events/stream?last_event_id=${lastEventId}`;
          controller = new AbortController();
          const user = JSON.parse(localStorage.getItem('user') || 'null');
          const blind = user?.role === 'hr' && localStorage.getItem(`blind_screening_hr_${user.id}`) === 'true';
          const response = await fetch(url, {
            signal: controller.signal,
            headers: {
              'Authorization': `Bearer ${token}`,
              ...(blind ? { 'X-Blind-Screening': 'true' } : {}),
            }
          });

          if (response.status === 401 || response.status === 403) {
            console.error("Realtime stream: authorization error");
            if (onStatusChange) onStatusChange('disconnected');
            if (onError) onError(new Error(`Unauthorized or Forbidden: Status ${response.status}`));
            break;
          }

          if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
          }

          if (onStatusChange) onStatusChange('connected');
          delay = 1000; // Reset reconnection delay on successful socket handshake

          reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          while (active) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const jsonStr = line.slice(6).trim();
                try {
                  const event = JSON.parse(jsonStr);
                  if (event.id) lastEventId = Math.max(lastEventId, event.id);
                  if (onEvent) onEvent(event);
                } catch (e) {
                  console.error("Realtime stream: JSON parse exception", e);
                }
              }
            }
          }
          if (active) throw new Error('Event stream closed');
        } catch (err) {
          if (!active) break;
          console.warn("Realtime stream error, scheduling reconnect...", err);
          if (onStatusChange) onStatusChange('disconnected');
          if (onError) onError(err);

          if (reader) {
            try {
              void reader.cancel().catch(() => {});
            } catch (e) {
              // ignore cancel error
            }
            reader = null;
          }

          // Await exponential reconnect timeout
          await new Promise((resolve) => {
            resolveReconnect = resolve;
            reconnectTimeout = setTimeout(resolve, delay);
          });
          reconnectTimeout = null;
          resolveReconnect = null;
          delay = Math.min(delay * 2, 30000);
        }
      }
    };

    runStream();

    return {
      abort: () => {
        active = false;
        controller?.abort();
        if (reader) {
          try {
            void reader.cancel().catch(() => {});
          } catch (e) {
            // ignore cancel error
          }
          reader = null;
        }
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
        resolveReconnect?.();
      }
    };
  }
};

export default realtimeService;
