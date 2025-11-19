import { useEffect, useRef, useState } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import type { realtimeUserData } from '@/domains/admin/types/rag.dashboard.types';

export interface CurrentMetricData {
  event: string;
  data: {
    value: number;
    total: number;
    deltaPct: number;
    direction: string;
  };
}

export type NewGroupData = {
  user: CurrentMetricData;
  document: CurrentMetricData;
  error: CurrentMetricData;
};

export interface MetricStreamPayload {
  accessUsers?: number;
  totalAccessUsers?: number;

  uploadedDocs?: number;
  totalUploadedDocs?: number;

  errorCount?: number;
  totalError?: number;

  deltaPct?: number;
  direction?: string;
}

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

export type NumberBoardConnected = Record<MetricKey, boolean>;
export type NumberBoardErrors = Partial<Record<MetricKey, string>>;

export function useNumberBoardStreams() {
  const token = useAuthStore.getState().accessToken;
  const base = import.meta.env.VITE_SPRING_BASE_URL;

  const [currentData, setCurrentData] = useState<NewGroupData | null>(null);
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

          const parsed = parseData<MetricStreamPayload>(evt.data);
          if (!parsed) return;

          let value = 0;
          let total = 0;
          const deltaPct = parsed.deltaPct ?? 0;
          const direction = parsed.direction ?? 'flat';

          // key에 따라 값 추출
          if (key === 'user') {
            value = parsed.accessUsers ?? 0;
            total = parsed.totalAccessUsers ?? 0;
          } else if (key === 'document') {
            value = parsed.uploadedDocs ?? 0;
            total = parsed.totalUploadedDocs ?? 0;
          } else if (key === 'error') {
            value = parsed.errorCount ?? 0;
            total = parsed.totalError ?? 0;
          }

          // state 업데이트
          setCurrentData((prev) => {
            const baseData: NewGroupData = prev ?? {
              user: {
                event: '',
                data: { value: 0, total: 0, deltaPct: 0, direction: 'flat' },
              },
              document: {
                event: '',
                data: { value: 0, total: 0, deltaPct: 0, direction: 'flat' },
              },
              error: {
                event: '',
                data: { value: 0, total: 0, deltaPct: 0, direction: 'flat' },
              },
            };

            return {
              ...baseData,
              [key]: {
                event: (evt as MessageEvent).type,
                data: {
                  value,
                  total,
                  deltaPct,
                  direction,
                },
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

export function useRealtimeUserStream() {
  const token = useAuthStore.getState().accessToken;
  const base = import.meta.env.VITE_SPRING_BASE_URL;
  const [errors, setErrors] = useState<NumberBoardErrors>({});
  const [realtimeUserData, setRealtimeUserData] = useState<realtimeUserData | null>(null);

  useEffect(() => {
    if (!token) return;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    };
    const url = `${base}/api/v1/user/active/realtime`;

    const es = new EventSourcePolyfill(url, {
      headers,
      withCredentials: true,
      heartbeatTimeout: 3600000,
    });
    const payloadListener: ESListener = {
      handleEvent(evt: Event) {
        if (!isMessageEventString(evt)) return;
        const parsed = parseData<realtimeUserData>(evt.data);
        if (!parsed) return;
        setRealtimeUserData(parsed);
      },
    };

    const errorListener: ESListener = {
      handleEvent() {
        setErrors({ user: 'SSE 연결 오류' });
      },
    };

    es.addEventListener('init', payloadListener);
    es.addEventListener('update', payloadListener);
    es.addEventListener('error', errorListener);

    return () => {
      es.removeEventListener('init', payloadListener);
      es.removeEventListener('update', payloadListener);
      es.removeEventListener('error', errorListener);
      es.close();
    };
  }, [token, base]);
  return { realtimeUserData, errors };
}
