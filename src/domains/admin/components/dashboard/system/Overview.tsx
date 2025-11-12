import { Cpu, HardDrive, Wifi, Coins } from 'lucide-react';
import type { ReactNode } from 'react';
import Card from '@/shared/components/Card';
import { useMonitoringStreams } from '@/domains/admin/hooks/useMonitoringStreams';
import {
  ExpenseList,
  type ModelExpense,
} from '@/domains/admin/components/dashboard/system/overview/ExpenseList';
import { NetworkMetrics } from './overview/NetworkMetrics';
import {
  StatCardContent,
  StatusPill,
  TimeRight,
} from '@/domains/admin/components/dashboard/system/overview/StatPrimitives';

function formatUsd(v?: number) {
  const n = typeof v === 'number' ? v : 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 3,
  }).format(n);
}

export default function Overview() {
  const {
    cpu,
    memory,
    network,
    expense,
    errors,
    connected,
    cpuBar,
    cpuBarColor,
    memBar,
    memBarColor,
    netBar,
  } = useMonitoringStreams();

  const stats: Array<{
    key: 'cpu' | 'mem' | 'net' | 'expense';
    title: string;
    subtitle?: string;
    status?: ReactNode;
    value: string | number;
    suffix?: string;
    icon: ReactNode;
    iconBg?: string;
    footer?: string;
    barValue?: number;
    barColor?: string;
    hints?: { leftLabel: string; leftValue: string; rightLabel: string; rightValue: string };
    topLeft?: ReactNode;
    topRight?: ReactNode;
    customContent?: ReactNode;
  }> = [
    {
      key: 'expense',
      title: '예상 비용',
      subtitle: '일일 모델 비용',
      status: connected.expense ? (
        <StatusPill ok text="실시간" />
      ) : errors.expense ? (
        <StatusPill warn text="연결 오류" />
      ) : (
        <StatusPill text="대기" />
      ),
      topLeft: <TimeRight ts={expense?.timestamp} />,
      value: formatUsd(expense?.grandPriceUsd),
      icon: <Coins size={22} className="text-[#10B981]" />,
      iconBg: 'bg-gradient-to-r from-[#ECFDF5]/90 to-white',
      customContent: expense?.models ? (
        <ExpenseList models={expense.models as ModelExpense[]} grand={expense?.grandPriceUsd} />
      ) : undefined,
    },
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
      topLeft: <TimeRight ts={cpu?.timestamp} />,
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
      topLeft: <TimeRight ts={memory?.timestamp} />,
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
      topLeft: <TimeRight ts={network?.timestamp} />,
      value:
        typeof network?.inboundMbps === 'number' ? Number(network.inboundMbps.toFixed(1)) : 103.3,
      suffix: 'Mbps IN',
      icon: <Wifi size={22} className="text-[#F97316]" />,
      iconBg: 'bg-gradient-to-r from-[#FFF7ED]/80 to-white',
      customContent: network ? (
        <div className="mt-2">
          <NetworkMetrics
            inboundMbps={Number(network.inboundMbps?.toFixed(1) ?? 0)}
            outboundMbps={Number(network.outboundMbps?.toFixed(1) ?? 0)}
            bandwidthMbps={network.bandwidthMbps}
            usagePercent={netBar}
          />
        </div>
      ) : null,
    },
  ];

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {stats.map((s) => (
        <Card
          key={s.key}
          title={s.title}
          subtitle={s.subtitle}
          icon={s.icon}
          iconBg={s.iconBg}
          status={s.status}
          className="p-4 max-h-[300px]"
        >
          <StatCardContent
            value={s.value}
            suffix={s.suffix}
            footer={s.footer}
            barValue={s.barValue}
            barColor={s.barColor}
            topLeft={s.topLeft}
            topRight={s.topRight}
            hints={s.hints}
            customContent={s.customContent}
          />
        </Card>
      ))}
    </section>
  );
}
