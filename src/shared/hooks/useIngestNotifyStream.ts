import { useEffect, useMemo, useRef, useState } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import type { IngestSummaryResponse } from '@/shared/types/ingest.types';

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null;
}

function isMessageEventString(evt: unknown): evt is MessageEvent<string> {
  return isRecord(evt) && 'data' in evt && typeof evt.data === 'string';
}

type ESListener = Parameters<EventSourcePolyfill['addEventListener']>[1];

function parseData<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export interface UseIngestNotifyStreamOptions {
  accessToken?: string;
  enabled?: boolean;
  urlOverride?: string;
  onMessage?: (data: IngestSummaryResponse) => void;
  onError?: (e: Event) => void;
}

export function useIngestNotifyStream({
  accessToken,
  enabled = true,
  urlOverride,
  onMessage,
  onError,
}: UseIngestNotifyStreamOptions) {
  const [connected, setConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);

  const esRef = useRef<EventSourcePolyfill | null>(null);
  const listenerRef = useRef<{
    payload?: ESListener;
    error?: ESListener;
  }>({});
  const onMessageRef = useRef<typeof onMessage>();
  const onErrorRef = useRef<typeof onError>();

  // 최신 콜백을 ref에만 저장 (deps에 안 넣음)
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const storeToken = useAuthStore.getState().accessToken;
  const token = useMemo(() => accessToken ?? storeToken ?? '', [accessToken, storeToken]);

  const base = import.meta.env.VITE_SPRING_BASE_URL;
  const url = useMemo(
    () => urlOverride ?? `${base}/api/v1/ingest/notify/stream`,
    [urlOverride, base]
  );

  useEffect(() => {
    // 토큰 없거나 꺼져 있으면 정리만
    if (!token || !enabled) {
      if (esRef.current && listenerRef.current.payload && listenerRef.current.error) {
        esRef.current.removeEventListener('ingest-summary-completed', listenerRef.current.payload);
        esRef.current.removeEventListener('message', listenerRef.current.payload);
        esRef.current.removeEventListener('error', listenerRef.current.error);
        esRef.current.close();
      }
      esRef.current = null;
      listenerRef.current = {};
      setConnected(false);
      return;
    }

    let cancelled = false;

    const cleanup = () => {
      if (esRef.current && listenerRef.current.payload && listenerRef.current.error) {
        esRef.current.removeEventListener('ingest-summary-completed', listenerRef.current.payload);
        esRef.current.removeEventListener('message', listenerRef.current.payload);
        esRef.current.removeEventListener('error', listenerRef.current.error);
        esRef.current.close();
      }
      esRef.current = null;
      listenerRef.current = {};
      setConnected(false);
    };

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    };

    const es = new EventSourcePolyfill(url, {
      headers,
      withCredentials: true,
      heartbeatTimeout: 3600000,
    });

    esRef.current = es;

    const payloadListener: ESListener = {
      handleEvent(evt: Event) {
        if (!isMessageEventString(evt)) return;
        const parsed = parseData<IngestSummaryResponse>(evt.data);
        if (!parsed) return;

        // 디버깅 로그
        console.log('[SSE] ingest event received:', parsed);

        setConnected(true);
        setLastError(null);
        if (onMessageRef.current) {
          onMessageRef.current(parsed);
        }
      },
    };

    const errorListener: ESListener = {
      handleEvent(evt: Event) {
        console.error('[SSE] ingest stream error event:', evt);
        setConnected(false);
        setLastError('SSE 연결 오류');
        if (onErrorRef.current) {
          onErrorRef.current(evt);
        }
      },
    };

    es.addEventListener('ingest-summary-completed', payloadListener);
    es.addEventListener('message', payloadListener);
    es.addEventListener('error', errorListener);

    listenerRef.current = {
      payload: payloadListener,
      error: errorListener,
    };

    es.onopen = () => {
      if (cancelled) return;
      console.log('[SSE] ingest stream opened');
      setConnected(true);
      setLastError(null);
    };

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [token, enabled, url]);

  return {
    connected,
    lastError,
  };
}
