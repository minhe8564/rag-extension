import { useEffect, useRef, useState } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import type { CurrentGroup } from '@/domains/admin/types/rag.dashboard.types';

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

type MetricKey = 'user' | 'document' | 'error';

type RawPayload = {
  accessUsers?: number;
  uploadedDocs?: number;
  errorCount?: number;
};

const fieldMap: Record<MetricKey, keyof RawPayload> = {
  user: 'accessUsers',
  document: 'uploadedDocs',
  error: 'errorCount',
};

export type NumberBoardConnected = Record<MetricKey, boolean>;
export type NumberBoardErrors = Partial<Record<MetricKey, string>>;

export function useNumberBoardStreams() {
  const token = useAuthStore.getState().accessToken;
  const base = import.meta.env.VITE_SPRING_BASE_URL;

  const [currentData, setCurrentData] = useState<CurrentGroup | null>(null);
  const [connected, setConnected] = useState<NumberBoardConnected>({
    user: false,
    document: false,
    error: false,
  });
  const [errors, setErrors] = useState<NumberBoardErrors>({});

  const esRefs = useRef<Partial<Record<MetricKey, EventSourcePolyfill | null>>>({});
  const listenersRef = useRef<
    Partial<Record<MetricKey, { payload: ESListener; error: ESListener }>>
  >({});

  const hasEverConnectedRef = useRef<Record<MetricKey, boolean>>({
    user: false,
    document: false,
    error: false,
  });

  useEffect(() => {
    if (!token) return;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    };

    const urls: Record<MetricKey, string> = {
      user: `${base}/api/v1/analytics/metrics/access-users/stream`,
      document: `${base}/api/v1/analytics/metrics/upload-documents/stream`,
      error: `${base}/api/v1/analytics/metrics/errors/stream`,
    };

    (Object.keys(urls) as MetricKey[]).forEach((key) => {
      const es = new EventSourcePolyfill(urls[key], {
        headers,
        withCredentials: true,
        heartbeatTimeout: 3600000,
      });
      esRefs.current[key] = es;

      const payloadListener: ESListener = {
        handleEvent(evt: Event) {
          if (!isMessageEventString(evt)) return;

          const parsed = parseData<RawPayload>(evt.data);
          if (!parsed) return;

          const field = fieldMap[key];
          const value = typeof parsed[field] === 'number' ? (parsed[field] as number) : 0;

          setCurrentData((prev) => {
            const baseData =
              prev ??
              ({
                user: { event: '', data: { accessUsers: 0 } },
                document: { event: '', data: { accessUsers: 0 } },
                error: { event: '', data: { accessUsers: 0 } },
              } as CurrentGroup);

            return {
              ...baseData,
              [key]: {
                event: (evt as MessageEvent).type,
                data: { accessUsers: value },
              },
            };
          });

          hasEverConnectedRef.current[key] = true;

          setConnected((c) => ({ ...c, [key]: true }));
          setErrors((e) => ({ ...e, [key]: undefined }));
        },
      };

      const errorListener: ESListener = {
        handleEvent() {
          setConnected((c) => ({ ...c, [key]: false }));
          setErrors((e) => {
            if (!hasEverConnectedRef.current[key]) {
              return { ...e, [key]: 'SSE 연결 오류' };
            }
            return e;
          });
        },
      };

      es.addEventListener('init', payloadListener);
      es.addEventListener('update', payloadListener);
      es.addEventListener('error', errorListener);

      listenersRef.current[key] = { payload: payloadListener, error: errorListener };
    });

    return () => {
      (Object.entries(esRefs.current) as [MetricKey, EventSourcePolyfill | null][]).forEach(
        ([key, es]) => {
          const listeners = listenersRef.current[key];
          if (es && listeners) {
            es.removeEventListener('init', listeners.payload);
            es.removeEventListener('update', listeners.payload);
            es.removeEventListener('error', listeners.error);
            es.close();
          }
        }
      );
      esRefs.current = {};
      listenersRef.current = {};
    };
  }, [token, base]);

  return { currentData, connected, errors };
}
