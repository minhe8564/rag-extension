// src/shared/hooks/useMonitoringStreams.ts
import { useEffect, useMemo, useRef, useState } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import type {
  CpuEvent,
  MemoryEvent,
  NetworkEvent,
  Errors,
  Connected,
  Streams,
  UseMonitoringStreamsOptions,
} from '@/domains/admin/types/system.dashboard.types';

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null;
}
function isMessageEventString(evt: unknown): evt is MessageEvent<string> {
  return (
    isRecord(evt) && 'data' in evt && typeof (evt as Record<string, unknown>).data === 'string'
  );
}

type ESListener = Parameters<EventSourcePolyfill['addEventListener']>[1];

function parseData<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function createPayloadListener<T>(
  setData: (d: T) => void,
  setConnected: (b: boolean) => void,
  setErrorText: (s: string | null) => void
): ESListener {
  const listenerObj = {
    handleEvent(evt: Event) {
      if (!isMessageEventString(evt)) return;
      const parsed = parseData<T>(evt.data);
      if (parsed) {
        setData(parsed);
        setConnected(true);
        setErrorText(null);
      }
    },
  };
  return listenerObj;
}

function createErrorListener(
  setConnectedKey: (b: boolean) => void,
  setErrorKey: (msg: string) => void
): ESListener {
  const listenerObj = {
    handleEvent(_evt: Event) {
      setConnectedKey(false);
      setErrorKey('SSE 연결 오류');
    },
  };
  return listenerObj;
}

export function useMonitoringStreams(opts: UseMonitoringStreamsOptions = {}) {
  const token = useAuthStore.getState().accessToken;
  const base = import.meta.env.VITE_SPRING_BASE_URL;
  console.log(base);

  const urls = useMemo<Required<Streams>>(
    () => ({
      cpu: opts.urls?.cpu ?? `${base}/api/v1/monitoring/cpu/stream`,
      memory: opts.urls?.memory ?? `${base}/api/v1/monitoring/memory/stream`,
      network: opts.urls?.network ?? `${base}/api/v1/monitoring/network/stream`,
    }),
    [opts.urls, base]
  );

  const [cpu, setCpu] = useState<CpuEvent | null>(null);
  const [memory, setMemory] = useState<MemoryEvent | null>(null);
  const [network, setNetwork] = useState<NetworkEvent | null>(null);

  const [errors, setErrors] = useState<Errors>({});
  const [connected, setConnected] = useState<Connected>({
    cpu: false,
    memory: false,
    network: false,
  });

  const esCpuRef = useRef<EventSourcePolyfill | null>(null);
  const esMemRef = useRef<EventSourcePolyfill | null>(null);
  const esNetRef = useRef<EventSourcePolyfill | null>(null);

  // 리스너 참조(클린업용)
  const listenersRef = useRef<{
    cpu?: { payload: ESListener; error: ESListener };
    memory?: { payload: ESListener; error: ESListener };
    network?: { payload: ESListener; error: ESListener };
  }>({});

  useEffect(() => {
    if (!token) return;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      Accept: 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    };
    const withCreds = opts.withCredentials ?? true;

    // CPU 스트림
    {
      const es = new EventSourcePolyfill(urls.cpu, { headers, withCredentials: withCreds });
      esCpuRef.current = es;

      const payloadListener = createPayloadListener<CpuEvent>(
        setCpu,
        (b) => setConnected((c) => ({ ...c, cpu: b })),
        (s) => setErrors((e) => ({ ...e, cpu: s }))
      );
      const errorListener = createErrorListener(
        (b) => setConnected((c) => ({ ...c, cpu: b })),
        (msg) => setErrors((e) => ({ ...e, cpu: msg }))
      );

      es.addEventListener('init', payloadListener);
      es.addEventListener('update', payloadListener);
      es.addEventListener('error', errorListener);

      listenersRef.current.cpu = { payload: payloadListener, error: errorListener };
    }

    // Memory 스트림
    {
      const es = new EventSourcePolyfill(urls.memory, { headers, withCredentials: withCreds });
      esMemRef.current = es;

      const payloadListener = createPayloadListener<MemoryEvent>(
        setMemory,
        (b) => setConnected((c) => ({ ...c, memory: b })),
        (s) => setErrors((e) => ({ ...e, memory: s }))
      );
      const errorListener = createErrorListener(
        (b) => setConnected((c) => ({ ...c, memory: b })),
        (msg) => setErrors((e) => ({ ...e, memory: msg }))
      );

      es.addEventListener('init', payloadListener);
      es.addEventListener('update', payloadListener);
      es.addEventListener('error', errorListener);

      listenersRef.current.memory = { payload: payloadListener, error: errorListener };
    }

    // Network 스트림
    {
      const es = new EventSourcePolyfill(urls.network, { headers, withCredentials: withCreds });
      esNetRef.current = es;

      const payloadListener = createPayloadListener<NetworkEvent>(
        setNetwork,
        (b) => setConnected((c) => ({ ...c, network: b })),
        (s) => setErrors((e) => ({ ...e, network: s }))
      );
      const errorListener = createErrorListener(
        (b) => setConnected((c) => ({ ...c, network: b })),
        (msg) => setErrors((e) => ({ ...e, network: msg }))
      );

      es.addEventListener('init', payloadListener);
      es.addEventListener('update', payloadListener);
      es.addEventListener('error', errorListener);

      listenersRef.current.network = { payload: payloadListener, error: errorListener };
    }

    return () => {
      // 이벤트 제거 + 연결 종료
      if (esCpuRef.current && listenersRef.current.cpu) {
        esCpuRef.current.removeEventListener('init', listenersRef.current.cpu.payload);
        esCpuRef.current.removeEventListener('update', listenersRef.current.cpu.payload);
        esCpuRef.current.removeEventListener('error', listenersRef.current.cpu.error);
        esCpuRef.current.close();
      }
      if (esMemRef.current && listenersRef.current.memory) {
        esMemRef.current.removeEventListener('init', listenersRef.current.memory.payload);
        esMemRef.current.removeEventListener('update', listenersRef.current.memory.payload);
        esMemRef.current.removeEventListener('error', listenersRef.current.memory.error);
        esMemRef.current.close();
      }
      if (esNetRef.current && listenersRef.current.network) {
        esNetRef.current.removeEventListener('init', listenersRef.current.network.payload);
        esNetRef.current.removeEventListener('update', listenersRef.current.network.payload);
        esNetRef.current.removeEventListener('error', listenersRef.current.network.error);
        esNetRef.current.close();
      }
      esCpuRef.current = null;
      esMemRef.current = null;
      esNetRef.current = null;
      listenersRef.current = {};
    };
  }, [token, urls.cpu, urls.memory, urls.network, opts.withCredentials]);

  // 편의 계산치
  const { cpuBar, cpuBarColor, memBar, memBarColor, netBar, netBarColor } = useMemo(() => {
    const _cpuBar = typeof cpu?.cpuUsagePercent === 'number' ? cpu.cpuUsagePercent : undefined;
    const _cpuBarColor =
      _cpuBar !== undefined
        ? _cpuBar >= 85
          ? 'bg-rose-500'
          : _cpuBar >= 60
            ? 'bg-amber-500'
            : 'bg-emerald-500'
        : 'bg-emerald-500';

    const _memBar =
      typeof memory?.memoryUsagePercent === 'number' ? memory.memoryUsagePercent : undefined;
    const _memBarColor =
      _memBar !== undefined
        ? _memBar >= 85
          ? 'bg-rose-500'
          : _memBar >= 60
            ? 'bg-amber-500'
            : 'bg-emerald-500'
        : 'bg-emerald-500';

    const netPct =
      network && network.bandwidthMbps
        ? (Math.max(network.inboundMbps, network.outboundMbps) / network.bandwidthMbps) * 100
        : undefined;

    const _netBar =
      typeof netPct === 'number'
        ? Math.min(100, Math.max(0, Number(netPct.toFixed(1))))
        : undefined;

    const _netBarColor =
      _netBar !== undefined
        ? _netBar >= 85
          ? 'bg-rose-500'
          : _netBar >= 60
            ? 'bg-amber-500'
            : 'bg-emerald-500'
        : 'bg-emerald-500';

    return {
      cpuBar: _cpuBar,
      cpuBarColor: _cpuBarColor,
      memBar: _memBar,
      memBarColor: _memBarColor,
      netBar: _netBar,
      netBarColor: _netBarColor,
    };
  }, [cpu, memory, network]);

  return {
    cpu,
    memory,
    network,
    errors,
    connected,
    cpuBar,
    cpuBarColor,
    memBar,
    memBarColor,
    netBar,
    netBarColor,
  };
}
