import { Cpu, HardDrive, Wifi } from 'lucide-react';
import type { ReactNode } from 'react';
import Card from '@/shared/components/Card';
import { useMonitoringStreams } from '@/domains/admin/hooks/useMonitoringStreams';

function ProgressBar({
  value,
  color = 'bg-emerald-500',
  showLabel = true,
}: {
  value: number;
  color?: string;
  showLabel?: boolean;
}) {
  const v = Math.min(100, Math.max(0, value));
  return (
    <div className="w-full">
      <div className="h-2 w-full rounded-full bg-gray-200">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${v}%` }} />
      </div>
      {showLabel && (
        <div className="mt-1 text-[11px] text-gray-500 text-right">{v.toFixed(0)}%</div>
      )}
    </div>
  );
}

function StatusPill({ ok, warn, text }: { ok?: boolean; warn?: boolean; text: string }) {
  const base = 'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs';
  const tone = ok
    ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100'
    : warn
      ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-100'
      : 'bg-gray-50 text-gray-600 ring-1 ring-gray-200';
  const dot = ok ? 'bg-emerald-500' : warn ? 'bg-amber-500' : 'bg-gray-300';
  return (
    <span className={`${base} ${tone}`}>
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {text}
    </span>
  );
}

function HintPair({
  leftLabel,
  leftValue,
  rightLabel,
  rightValue,
}: {
  leftLabel: string;
  leftValue: string;
  rightLabel: string;
  rightValue: string;
}) {
  return (
    <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
      <div className="rounded-xl bg-gray-50 px-3 py-2">
        <div className="text-[11px] text-gray-500">{leftLabel}</div>
        <div className="font-medium text-gray-800">{leftValue}</div>
      </div>
      <div className="rounded-xl bg-gray-50 px-3 py-2">
        <div className="text-[11px] text-gray-500">{rightLabel}</div>
        <div className="font-medium text-gray-800">{rightValue}</div>
      </div>
    </div>
  );
}

function StatCardContent({
  value,
  suffix,
  footer,
  barValue,
  barColor = 'bg-emerald-500',
  topRight,
  hints,
}: {
  value: string | number;
  suffix?: string;
  footer?: string;
  barValue?: number;
  barColor?: string;
  topRight?: ReactNode;
  hints?: { leftLabel: string; leftValue: string; rightLabel: string; rightValue: string };
}) {
  return (
    <>
      <div className="flex items-start justify-between">
        <div className="text-3xl font-semibold text-gray-900">
          {value}
          {suffix && <span className="ml-1 text-lg font-medium text-gray-500">{suffix}</span>}
        </div>
        {topRight}
      </div>

      {typeof barValue === 'number' && (
        <div className="mt-3">
          <ProgressBar value={barValue} color={barColor} />
        </div>
      )}

      {hints && (
        <HintPair
          leftLabel={hints.leftLabel}
          leftValue={hints.leftValue}
          rightLabel={hints.rightLabel}
          rightValue={hints.rightValue}
        />
      )}

      {footer && <div className="mt-3 text-xs text-gray-500">{footer}</div>}
    </>
  );
}

function TimeRight({ ts }: { ts?: string }) {
  if (!ts) return null;
  return (
    <div className="text-[11px] text-gray-500">
      {new Date(ts).toLocaleTimeString('ko-KR', { hour12: false })}
    </div>
  );
}

export default function Overview() {
  const {
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
  } = useMonitoringStreams();

  const stats: Array<{
    key: 'cpu' | 'mem' | 'net';
    title: string;
    subtitle?: string;
    status?: string | ReactNode;
    value: string | number;
    suffix?: string;
    icon: ReactNode;
    iconBg?: string;
    footer?: string;
    barValue?: number;
    barColor?: string;
    hints?: { leftLabel: string; leftValue: string; rightLabel: string; rightValue: string };
    topRight?: ReactNode;
  }> = [
    {
      key: 'cpu',
      title: 'CPU 사용률',
      subtitle: '평균',
      status: connected.cpu ? (
        <StatusPill ok text="실시간" />
      ) : errors.cpu ? (
        <StatusPill warn text="연결 오류" />
      ) : (
        <StatusPill text="대기" />
      ),
      value: typeof cpu?.cpuUsagePercent === 'number' ? Number(cpu.cpuUsagePercent.toFixed(1)) : 78,
      suffix: '%',
      icon: <Cpu size={22} className="text-[#5A8CFF]" />,
      iconBg: 'bg-gradient-to-r from-[#E3EDFF]/70 to-[#CBE1FF]/70',
      footer: cpu
        ? `${cpu.totalCores}코어 중 활성 ${cpu.activeCores}코어`
        : errors.cpu
          ? '연결 오류 · 재시도 중'
          : '8 코어 사용 중',
      barValue: cpuBar,
      barColor: cpuBarColor,
      hints: cpu
        ? {
            leftLabel: '총 코어',
            leftValue: String(cpu.totalCores),
            rightLabel: '활성 코어',
            rightValue: String(cpu.activeCores),
          }
        : undefined,
      topRight: <TimeRight ts={cpu?.timestamp} />,
    },
    {
      key: 'mem',
      title: '메모리 사용량',
      subtitle: 'RAM',
      status: connected.memory ? (
        <StatusPill ok text="실시간" />
      ) : errors.memory ? (
        <StatusPill warn text="연결 오류" />
      ) : (
        <StatusPill text="대기" />
      ),
      value:
        typeof memory?.usedMemoryGB === 'number' ? Number(memory.usedMemoryGB.toFixed(1)) : 3.8,
      suffix: 'GB',
      icon: <HardDrive size={22} className="text-[#8B5CF6]" />,
      iconBg: 'bg-gradient-to-r from-white to-[#EDE9FE]/70',
      footer: memory
        ? `사용률 ${Number(memory.memoryUsagePercent.toFixed(1))}%`
        : '총 8GB 중 47% 사용',
      barValue: memBar,
      barColor: memBarColor,
      hints: memory
        ? {
            leftLabel: '총 메모리',
            leftValue: `${memory.totalMemoryGB} GB`,
            rightLabel: '사용률',
            rightValue: `${Number(memory.memoryUsagePercent.toFixed(1))}%`,
          }
        : undefined,
      topRight: <TimeRight ts={memory?.timestamp} />,
    },
    {
      key: 'net',
      title: '네트워크',
      subtitle: '트래픽',
      status: connected.network ? (
        <StatusPill ok text="실시간" />
      ) : errors.network ? (
        <StatusPill warn text="연결 오류" />
      ) : (
        <StatusPill text="대기" />
      ),
      value:
        typeof network?.inboundMbps === 'number' ? Number(network.inboundMbps.toFixed(1)) : 103.3,
      suffix: 'Mbps IN',
      icon: <Wifi size={22} className="text-[#F97316]" />,
      iconBg: 'bg-gradient-to-r from-[#FFF7ED]/80 to-white',
      footer: network ? `대역폭 ${network.bandwidthMbps} Mbps` : '대역폭: 1Gbps',
      barValue: netBar,
      barColor: netBarColor,
      hints: network
        ? {
            leftLabel: 'OUT',
            leftValue: `${Number(network.outboundMbps.toFixed(1))} Mbps`,
            rightLabel: '대역폭 사용',
            rightValue: netBar !== undefined ? `${netBar.toFixed(0)}%` : '-',
          }
        : undefined,
      topRight: <TimeRight ts={network?.timestamp} />,
    },
  ];

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {stats.map((s) => (
        <Card
          key={s.key}
          title={s.title}
          subtitle={typeof s.subtitle === 'string' ? s.subtitle : undefined}
          icon={s.icon}
          iconBg={s.iconBg}
          className="p-4"
        >
          {typeof s.status !== 'string' && <div className="mb-2">{s.status}</div>}
          <StatCardContent
            value={s.value}
            suffix={s.suffix}
            footer={s.footer}
            barValue={s.barValue}
            barColor={s.barColor}
            topRight={s.topRight}
            hints={s.hints}
          />
        </Card>
      ))}
    </section>
  );
}
