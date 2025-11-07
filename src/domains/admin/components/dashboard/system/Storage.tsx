import { CheckCircle2, AlertTriangle, HardDrive } from 'lucide-react';
import Card from '@/shared/components/Card';

type Status = 'healthy' | 'warning' | 'error';

function ServiceItem({ name, status, uptime }: { name: string; status: Status; uptime: string }) {
  const dot =
    status === 'healthy' ? 'bg-emerald-500' : status === 'warning' ? 'bg-amber-500' : 'bg-rose-500';
  const label =
    status === 'healthy' ? (
      <span className="inline-flex items-center gap-1 text-emerald-700">
        <CheckCircle2 size={14} /> Running
      </span>
    ) : status === 'warning' ? (
      <span className="inline-flex items-center gap-1 text-amber-700">
        <AlertTriangle size={14} /> Degraded
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 text-rose-700">
        <AlertTriangle size={14} /> Stopped
      </span>
    );

  return (
    <div className="flex items-center justify-between py-2">
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
  const v = Math.min(100, Math.max(0, value));
  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
    </div>
  );
}

export default function Storage({ className = '' }: { className?: string }) {
  const services = [
    { name: 'Web Server', status: 'healthy' as Status, uptime: '15d 4h' },
    { name: 'Database', status: 'healthy' as Status, uptime: '30d 12h' },
    { name: 'Redis Cache', status: 'healthy' as Status, uptime: '7d 18h' },
    { name: 'Message Queue', status: 'error' as Status, uptime: '-' },
    { name: 'Load Balancer', status: 'healthy' as Status, uptime: '45d 6h' },
    { name: 'Monitoring', status: 'healthy' as Status, uptime: '2d 8h' },
  ];

  const storage = [
    { mount: '/', label: '/ (Root)', total: '100GB', usedPct: 78, free: '22GB' },
    { mount: '/var/log', label: '/var/log', total: '50GB', usedPct: 45, free: '27.5GB' },
    { mount: '/data', label: '/data', total: '500GB', usedPct: 92, free: '40GB' },
    { mount: '/backup', label: '/backup', total: '1TB', usedPct: 23, free: '770GB' },
  ];

  const colorBy = (p: number) =>
    p >= 85 ? 'bg-rose-500' : p >= 60 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <section className={`grid grid-cols-1 xl:grid-cols-2 gap-6 ${className}`}>
      <Card>
        <div className="mb-6">
          <div className="flex items-center gap-3 text-gray-800">
            <CheckCircle2 size={22} className="text-emerald-500" />
            <h3 className="text-xl font-semibold text-gray-900">서비스 상태</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">실행 중인 서비스 현황</p>
        </div>

        <div className="divide-y divide-gray-100">
          {services.map((svc) => (
            <ServiceItem key={svc.name} {...svc} />
          ))}
        </div>

        <div className="mt-4 rounded-lg border border-emerald-100 p-3 text-xs text-gray-600">
          활성 서비스: <span className="font-medium text-gray-800">24/28</span>
          <span className="ml-2">·</span>
          <span className="ml-2">86% 가동 중</span>
        </div>
      </Card>

      <Card>
        <div className="mb-6">
          <div className="flex items-center gap-3 text-gray-800">
            <HardDrive size={18} className="text-violet-500" />
            <h3 className="text-xl font-semibold text-gray-900">스토리지 현황</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">디스크 사용량 및 용량</p>
        </div>

        <div className="mt-4 space-y-4">
          {storage.map((d) => (
            <div key={d.mount} className="rounded-xl bg-gray-50 p-4 ring-1 ring-gray-100">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-gray-800">{d.label}</div>
                <div className="text-xs text-gray-500">{d.usedPct}% 사용</div>
              </div>
              <div className="mt-2">
                <ProgressBar value={d.usedPct} color={colorBy(d.usedPct)} />
              </div>
              <div className="mt-1 flex justify-between text-[11px] text-gray-500">
                <span>총 용량: {d.total}</span>
                <span>여유 공간: {d.free}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
