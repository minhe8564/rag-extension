import { EventSourcePolyfill } from 'event-source-polyfill';

export function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null;
}

export function isMessageEventString(evt: unknown): evt is MessageEvent<string> {
  return isRecord(evt) && 'data' in evt && typeof evt.data === 'string';
}

export function parseData<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export type ESListener = Parameters<EventSourcePolyfill['addEventListener']>[1];
