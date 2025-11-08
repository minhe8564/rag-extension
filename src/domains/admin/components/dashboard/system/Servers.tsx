import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { Server, RefreshCw } from 'lucide-react';
import Card from '@/shared/components/Card';
import { getServicesPerformance } from '@/domains/admin/api/system.dashboard.api';
import type { ServicePerformance, PerfLevel } from '@/domains/admin/types/system.dashboard.types';

const tone: Record<PerfLevel, { bg: string; ring: string; dot: string; bar: string }> = {
  NORMAL: {
    bg: 'bg-emerald-50',
    ring: 'ring-emerald-100',
    dot: 'bg-emerald-500',
    bar: 'bg-emerald-500',
  },
  WARNING: { bg: 'bg-amber-50', ring: 'ring-amber-100', dot: 'bg-amber-500', bar: 'bg-amber-500' },
  CRITICAL: { bg: 'bg-rose-50', ring: 'ring-rose-100', dot: 'bg-rose-500', bar: 'bg-rose-500' },
};

function ProgressBar({ value, color }: { value: number; color: string }) {
  const v = Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0;
  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
    </div>
  );
}

function ServiceCard({ service }: { service: ServicePerformance }) {
  const t = tone[service.status];
  const pct = (n: unknown, digits = 1) =>
    // typeof n === 'number' && Number.isFinite(n) ? `${(n * 100).toFixed(digits)}%` : 'N/A';
    typeof n === 'number' && Number.isFinite(n) ? `${(n * 10).toFixed(digits)}%` : 'N/A';

  // const cpuPct = (service.cpuUsagePercent ?? 0) * 100;
  // const memPct = (service.memoryUsagePercent ?? 0) * 100;
  // const score = (service.compositeScore ?? 0) * 100;
  const cpuPct = (service.cpuUsagePercent ?? 0) * 10;
  const memPct = (service.memoryUsagePercent ?? 0) * 10;
  const score = (service.compositeScore ?? 0) * 10;

  return (
    <div className={`rounded-xl ${t.bg} ring-1 ${t.ring} p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${t.dot}`} />
          <div className="font-medium text-gray-800">{service.serviceName}</div>
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="text-xs text-gray-500">CPU</div>
        <ProgressBar value={cpuPct} color={t.bar} />
        <div className="text-right text-xs text-gray-500">{pct(service.cpuUsagePercent)}</div>

        <div className="mt-2 text-xs text-gray-500">Memory</div>
        <ProgressBar value={memPct} color={t.bar} />
        <div className="text-right text-xs text-gray-500">{pct(service.memoryUsagePercent)}</div>

        <div className="mt-2 text-xs text-gray-500">
          통합점수 <span className="font-medium text-gray-800">{score.toFixed(1)}</span> · 상태{' '}
          <span className="font-medium text-gray-800">{service.status ?? '-'}</span>
        </div>
      </div>
    </div>
  );
}

export default function Servers({ className = '' }: { className?: string }) {
  const [services, setServices] = useState<ServicePerformance[]>([]);
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const fetchOnce = async () => {
    try {
      setErrorText(null);
      setRefreshing(true);
      const result = await getServicesPerformance(); // { timestamp, services }
      setServices(result?.services ?? []);
      setTimestamp(result?.timestamp ?? null);
    } catch {
      setErrorText('데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    abortRef.current = new AbortController();
    fetchOnce();
    const timer = setInterval(fetchOnce, 60_000); // 1분 폴링
    return () => {
      abortRef.current?.abort();
      clearInterval(timer);
    };
  }, []);

  const lastTime = useMemo(
    () => (timestamp ? new Date(timestamp).toLocaleTimeString('ko-KR', { hour12: false }) : ''),
    [timestamp]
  );

  return (
    <Card className={className}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--color-hebees-bg)] flex items-center justify-center">
            <Server size={20} className="text-[var(--color-hebees)]" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-900">서비스 인스턴스 모니터링</h3>
            <p className="text-sm text-gray-500">개별 서비스 성능 및 상태</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 text-sm text-gray-500">
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500" /> 정상
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500" /> 주의
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-rose-500" /> 위험
            </span>

            <button
              type="button"
              onClick={fetchOnce}
              disabled={refreshing}
              className={clsx(
                'flex items-center gap-1.5 text-sm rounded-md px-3 py-1',
                'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <RefreshCw size={14} className={clsx(refreshing && 'animate-spin')} />
              {refreshing ? '불러오는 중...' : '새로고침'}
            </button>
          </div>

          {lastTime && <span className="text-xs text-gray-400 mt-0.5">기준: {lastTime}</span>}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl bg-gray-50 ring-1 ring-gray-100 p-4 animate-pulse h-40"
            />
          ))}
        </div>
      ) : errorText ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-700 text-sm">
          {errorText}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {services.map((sv) => (
            <ServiceCard key={sv.serviceName} service={sv} />
          ))}
        </div>
      )}
    </Card>
  );
}
