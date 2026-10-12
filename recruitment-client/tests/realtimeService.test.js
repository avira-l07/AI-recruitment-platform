import test from 'node:test';
import assert from 'node:assert/strict';
import realtimeService from '../src/services/realtimeService.js';

const tick = () => new Promise(resolve => setImmediate(resolve));

test('aborting a pending connection cancels fetch', async (t) => {
  const oldFetch = globalThis.fetch;
  const oldStorage = globalThis.localStorage;
  t.after(() => { globalThis.fetch = oldFetch; globalThis.localStorage = oldStorage; });
  globalThis.localStorage = { getItem: () => null };
  let signal;
  globalThis.fetch = async (_url, options) => {
    signal = options.signal;
    return new Promise((_resolve, reject) => signal.addEventListener('abort', () => reject(new Error('aborted'))));
  };
  const stream = realtimeService.connectEventStream('token', 0, () => {});
  stream.abort();
  await tick();
  assert.equal(signal.aborted, true);
});

test('reconnect resumes after the latest event and sends blind mode preference', async (t) => {
  const oldFetch = globalThis.fetch;
  const oldStorage = globalThis.localStorage;
  const oldTimer = globalThis.setTimeout;
  const oldWarning = console.warn;
  let reconnect;
  t.after(() => { globalThis.fetch = oldFetch; globalThis.localStorage = oldStorage; globalThis.setTimeout = oldTimer; console.warn = oldWarning; });
  console.warn = () => {};
  globalThis.localStorage = { getItem: key => key === 'user' ? JSON.stringify({ id: 1, role: 'hr' }) : 'true' };
  globalThis.setTimeout = callback => { reconnect = callback; return 1; };
  const urls = [];
  const events = [];
  globalThis.fetch = async (url, options) => {
    urls.push(url);
    assert.equal(options.headers['X-Blind-Screening'], 'true');
    if (urls.length > 1) return new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted'))));
    let read = 0;
    return { ok: true, status: 200, body: { getReader: () => ({
      read: async () => read++ === 0 ? { value: new TextEncoder().encode('data: {"id":7}\n\n'), done: false } : { done: true },
      cancel: async () => {},
    }) } };
  };
  const stream = realtimeService.connectEventStream('token', 2, event => events.push(event));
  await tick();
  assert.equal(events[0].id, 7);
  assert.equal(typeof reconnect, 'function');
  reconnect();
  await tick();
  assert.match(urls[1], /last_event_id=7$/);
  stream.abort();
  await tick();
});
