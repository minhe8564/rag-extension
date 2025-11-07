import { Server } from 'lucide-react';
import Card from '@/shared/components/Card';

type Status = 'healthy' | 'warning' | 'error';
const theme: Record<Status, { bg: string; ring: string; dot: string; bar: string }> = {
  healthy: {
    bg: 'bg-emerald-50',
    ring: 'ring-emerald-100',
    dot: 'bg-emerald-500',
    bar: 'bg-emerald-500',
  },
  warning: { bg: 'bg-amber-50', ring: 'ring-amber-100', dot: 'bg-amber-500', bar: 'bg-amber-500' },
  error: { bg: 'bg-rose-50', ring: 'ring-rose-100', dot: 'bg-rose-500', bar: 'bg-rose-500' },
};

function ProgressBar({ value, color }: { value: number; color: string }) {
  const v = Math.min(100, Math.max(0, value));
  return (
    <div className="h-2 w-full rounded-full bg-gray-200">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
    </div>
  );
}

function ServerCard({
  name,
  load,
  cpu,
  memory,
  status,
}: {
  name: string;
  load: number;
  cpu: number;
  memory: number;
  status: Status;
}) {
  const t = theme[status];
  return (
    <div className={`rounded-xl ${t.bg} ring-1 ${t.ring} p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${t.dot}`} />
          <div className="font-medium text-gray-800">{name}</div>
        </div>
        <div className="text-xs text-gray-500">
          Load <span className="font-medium text-gray-800">{load.toFixed(1)}</span>
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="text-xs text-gray-500">CPU</div>
        <ProgressBar value={cpu} color={t.bar} />
        <div className="text-right text-[11px] text-gray-500">{cpu}%</div>

        <div className="mt-2 text-xs text-gray-500">Memory</div>
        <ProgressBar value={memory} color={t.bar} />
        <div className="text-right text-[11px] text-gray-500">{memory}%</div>
      </div>
    </div>
  );
}

export default function Servers({ className = '' }: { className?: string }) {
  const servers = [
    { name: 'Web-01', load: 1.2, cpu: 19, memory: 77, status: 'healthy' as Status },
    { name: 'Web-02', load: 1.5, cpu: 47, memory: 69, status: 'healthy' as Status },
    { name: 'API-01', load: 0.9, cpu: 88, memory: 87, status: 'warning' as Status },
    { name: 'DB-01', load: 1.2, cpu: 51, memory: 60, status: 'healthy' as Status },
    { name: 'Cache-01', load: 0.0, cpu: 20, memory: 18, status: 'healthy' as Status },
    { name: 'Queue-01', load: 1.9, cpu: 42, memory: 63, status: 'error' as Status },
  ];

  return (
    <Card>
      <div className="flex items-center justify-between mb-10">
        <div>
          <div className="flex items-center gap-3 text-gray-800">
            <Server size={22} className="text-[#A35FD3]" />
            <h3 className="text-xl font-semibold text-gray-900">서비스 인스턴스 모니터링</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">개별 서비스 성능 및 상태</p>
        </div>

        <div className="text-sm text-gray-500 flex items-center gap-4">
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> 정상
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> 주의
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-rose-500" /> 위험
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {servers.map((sv) => (
          <ServerCard key={sv.name} {...sv} />
        ))}
      </div>
    </Card>
  );
}
