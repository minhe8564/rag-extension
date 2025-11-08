import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { CheckCircle2, AlertTriangle, HardDrive, RefreshCw } from 'lucide-react';
import Card from '@/shared/components/Card';
import { getServicesStatus, getStorageUsage } from '@/domains/admin/api/system.dashboard.api';
import type {
  ServicesStatusResult,
  StorageUsageResult,
} from '@/domains/admin/types/system.dashboard.types';

type UiStatus = 'healthy' | 'warning' | 'error';

type ServiceStatus = ServicesStatusResult['services'][number]['status'];

function mapUiStatus(s: ServiceStatus): UiStatus {
  // RUNNING → healthy, STOPPED → error, UNKNOWN → warning
  if (s === 'RUNNING') return 'healthy';
  if (s === 'STOPPED') return 'error';
  return 'warning';
}

function ServiceItem({ name, ui, uptime }: { name: string; ui: UiStatus; uptime: string }) {
  const dot =
    ui === 'healthy' ? 'bg-emerald-500' : ui === 'warning' ? 'bg-amber-500' : 'bg-rose-500';
  const label =
    ui === 'healthy' ? (
      <span className="inline-flex items-center gap-1 text-emerald-700">
        <CheckCircle2 size={14} /> Running
      </span>
    ) : ui === 'warning' ? (
      <span className="inline-flex items-center gap-1 text-amber-700">
        <AlertTriangle size={14} /> Unknown
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-rose-700">
        <AlertTriangle size={14} /> Stopped
      </span>
    );

  return (
    <div className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
        <span className="text-sm text-gray-800">{name}</span>
      </div>
      <div className="text-xs text-gray-500 flex items-center gap-3">
        <span>{label}</span>
        <span className="text-gray-400">Uptime: {uptime}</span>
      </div>
    </div>
  );
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  const v = Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0;
  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
    </div>
  );
}

export default function Storage({ className = '' }: { className?: string }) {
  const [svcData, setSvcData] = useState<ServicesStatusResult | null>(null);
  const [fsData, setFsData] = useState<StorageUsageResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchAll = async () => {
    try {
      setErrorText(null);
      setRefreshing(true);
      const [svc, fs] = await Promise.all([getServicesStatus(), getStorageUsage()]);
      setSvcData(svc ?? null);
      setFsData(fs ?? null);
    } catch {
      setErrorText('모니터링 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    abortRef.current = new AbortController();
    fetchAll();
    const timer = setInterval(fetchAll, 60_000);
    return () => {
      abortRef.current?.abort();
      clearInterval(timer);
    };
  }, []);

  const lastTime = useMemo(() => {
    const ts = [svcData?.timestamp, fsData?.timestamp]
      .filter(Boolean)
      .map((t) => new Date(String(t)).getTime());
    if (!ts.length) return '';
    const max = new Date(Math.max(...ts));
    return max.toLocaleTimeString('ko-KR', { hour12: false });
  }, [svcData?.timestamp, fsData?.timestamp]);

  const colorBy = (p: number) =>
    p >= 85 ? 'bg-rose-500' : p >= 60 ? 'bg-amber-500' : 'bg-emerald-500';

  const runningCount = useMemo(
    () => svcData?.services.filter((s) => s.status === 'RUNNING').length ?? 0,
    [svcData]
  );
  const totalCount = svcData?.services.length ?? 0;
  const runningPct = totalCount ? Math.round((runningCount / totalCount) * 100) : 0;

  return (
    <section className={`grid grid-cols-1 xl:grid-cols-2 gap-6 ${className}`}>
      <Card className="relative">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="text-gray-800">
              <div className="flex items-start gap-3">
                <CheckCircle2 size={22} className="text-emerald-500 mt-1" />
                <h3 className="text-xl font-semibold text-gray-900">서비스 상태</h3>
              </div>
              <p className="text-sm text-gray-500 mt-1">실행 중인 서비스 현황</p>
            </div>

            <div className="flex flex-col items-end gap-1">
              <button
                type="button"
                onClick={fetchAll}
                disabled={loading || refreshing}
                className={clsx(
                  'inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-sm',
                  'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <RefreshCw size={14} className={clsx(refreshing && 'animate-spin')} />
                {refreshing ? '갱신 중…' : '새로고침'}
              </button>
              {lastTime && <span className="text-xs mt-1 text-gray-400">기준: {lastTime}</span>}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-10 rounded-lg bg-gray-50 ring-1 ring-gray-100 animate-pulse"
              />
            ))}
          </div>
        ) : errorText ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-700 text-sm">
            {errorText}
          </div>
        ) : (
          <>
            <div className="divide-y divide-gray-100">
              {svcData?.services.map((s) => (
                <ServiceItem
                  key={s.serviceName}
                  name={s.serviceName}
                  ui={mapUiStatus(s.status)}
                  uptime={s.uptimeSeconds ?? null}
                />
              ))}
            </div>
            <div className="mt-4 rounded-xl border border-blue-200 bg-gradient-to-br from-[#F8FAFF] to-[#F0F6FF] px-6 py-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
                    <CheckCircle2 size={14} className="text-blue-500" />
                    서비스 가동률
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    활성 서비스 {runningCount}/{totalCount}
                  </p>
                </div>

                <p className="text-[28px] font-bold text-gray-900 leading-none">{runningPct}%</p>
              </div>

              <div className="mt-4 h-[6px] w-full bg-blue-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${runningPct}%` }}
                />
              </div>
            </div>
          </>
        )}
      </Card>

      <Card>
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="text-gray-800">
              <div className="flex items-start gap-3">
                <HardDrive size={18} className="text-violet-500 mt-1" />
                <h3 className="text-xl font-semibold text-gray-900">스토리지 현황</h3>
              </div>
              <p className="text-sm text-gray-500 mt-1">디스크 사용량 및 용량</p>
            </div>

            <div className="flex flex-col items-end gap-1">
              <button
                type="button"
                onClick={fetchAll}
                disabled={loading || refreshing}
                className={clsx(
                  'inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-sm',
                  'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <RefreshCw size={14} className={clsx(refreshing && 'animate-spin')} />
                {refreshing ? '갱신 중…' : '새로고침'}
              </button>
              {lastTime && <span className="text-xs mt-1 text-gray-400">기준: {lastTime}</span>}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-20 rounded-xl bg-gray-50 ring-1 ring-gray-100 animate-pulse"
              />
            ))}
          </div>
        ) : errorText ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-700 text-sm">
            {errorText}
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {fsData?.fileSystems.map((fs) => (
              <div key={fs.path} className="rounded-xl bg-gray-50 p-4 ring-1 ring-gray-100">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-gray-800">{fs.path}</div>

                  <div className="text-sm font-semibold text-gray-700">
                    {fs.usagePercent.toFixed(1)}%
                    <span className="text-xs font-normal text-gray-500 ml-0.5"> 사용</span>
                  </div>
                </div>

                <div className="mt-2">
                  <ProgressBar value={fs.usagePercent} color={colorBy(fs.usagePercent)} />
                </div>

                <div className="mt-2 flex justify-between text-xs text-gray-500">
                  <span>총 용량: {fs.totalGB} GB</span>
                  <span>사용량: {fs.usedGB} GB</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </section>
  );
}
