import { useState, useEffect, useRef } from 'react';
import authService from '../services/authService';
import analyticsService from '../services/analyticsService';
import realtimeService from '../services/realtimeService';

export const useHRRealtime = (onNewEventTrigger) => {
  const [events, setEvents] = useState([]);
  const [streamStatus, setStreamStatus] = useState('disconnected');
  const seenEventIdsRef = useRef(new Set());
  const lastSeenIdRef = useRef(0);
  const token = authService.getToken();

  // Create a ref for onNewEventTrigger so the useEffect doesn't trigger repeatedly when callback reference changes
  const onNewEventTriggerRef = useRef(onNewEventTrigger);
  useEffect(() => {
    onNewEventTriggerRef.current = onNewEventTrigger;
  }, [onNewEventTrigger]);

  useEffect(() => {
    if (!token) return;
    let active = true;
    let stream = null;

    const initializeRealtime = async () => {
      try {
        // Step 1: Preload history logs (cap at 10 for dashboard overview feed)
        const history = await analyticsService.getEvents(10);
        if (active && Array.isArray(history)) {
          history.forEach((ev) => {
            if (ev.id) {
              seenEventIdsRef.current.add(ev.id);
              if (ev.id > lastSeenIdRef.current) {
                lastSeenIdRef.current = ev.id;
              }
            }
          });
          setEvents(history);
        }
      } catch (err) {
        console.warn("Failed to load initial event history", err);
      }

      // Step 2: Establish the authenticated SSE event stream AFTER the captured max history ID
      if (active) {
        stream = realtimeService.connectEventStream(
          token,
          lastSeenIdRef.current,
          (event) => {
            if (!active) return;
            if (event.id && !seenEventIdsRef.current.has(event.id)) {
              seenEventIdsRef.current.add(event.id);
              if (event.id > lastSeenIdRef.current) {
                lastSeenIdRef.current = event.id;
              }
              setEvents((prev) => [event, ...prev].slice(0, 50));
              if (onNewEventTriggerRef.current) {
                onNewEventTriggerRef.current(event);
              }
            }
          },
          (err) => {
            console.warn("Realtime stream error handler:", err);
          },
          (status) => {
            if (active) setStreamStatus(status);
          }
        );
      }
    };

    initializeRealtime();

    // StrictMode cleanup proof: cancel/abort connection and clear reconnect schedules immediately
    return () => {
      active = false;
      if (stream) {
        stream.abort();
        stream = null;
      }
    };
  }, [token]);

  return { events, streamStatus };
};
