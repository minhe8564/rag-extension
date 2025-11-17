import { useState, useEffect } from 'react';
import {
  Users,
  FileText,
  TriangleAlert,
  TrendingUp,
  TrendingDown,
  DatabaseZap,
} from 'lucide-react';
import {
  getTotalUserCount,
  getUserChangeTrend,
  getTotalDocumentCount,
  getDocumentChangeTrend,
  getTotalErrorCount,
  getErrorChangeTrend,
} from '@/domains/admin/api/rag.dashboard.api';
import type { TrendGroup, TotalGroup } from '@/domains/admin/types/rag.dashboard.types';
import {
  useNumberBoardStreams,
  useRealtimeUserStream,
} from '@/domains/admin/hooks/useNumberBoardStreams';
import {
  StatusPill,
  TimeRight,
} from '@/domains/admin/components/dashboard/system/overview/StatPrimitives';

export default function NumberBoard() {
  const { currentData, connected, errors } = useNumberBoardStreams();
  const { realtimeUserData } = useRealtimeUserStream();
  const [totalData, setTotalData] = useState<TotalGroup | null>(null);
  const [trendData, setTrendData] = useState<TrendGroup | null>(null);

  useEffect(() => {
    const fetchTotalData = async () => {
      const [totalUserData, totalDocumentData, totalErrorData] = await Promise.all([
        getTotalUserCount(),
        getTotalDocumentCount(),
        getTotalErrorCount(),
      ]);

      const normalziedTotalUserData: TotalGroup = {
        user: { totalUser: totalUserData.totalUser, asOf: totalUserData.asOf },
        document: { totalDocs: totalDocumentData.totalDocs, asOf: totalDocumentData.asOf },
        error: { totalErrors: totalErrorData.totalErrors, asOf: totalErrorData.asOf },
      };
      setTotalData(normalziedTotalUserData);
    };

    const fetchTrendData = async () => {
      const [trendUserData, trendDocumentData, trendErrorData] = await Promise.all([
        getUserChangeTrend(),
        getDocumentChangeTrend(),
        getErrorChangeTrend(),
      ]);

      const normalziedTrendUserData: TrendGroup = {
        user: {
          todayTotal: trendUserData.todayTotal,
          yesterdayTotal: trendUserData.yesterdayTotal,
          deltaPct: trendUserData.deltaPct,
          direction: trendUserData.direction,
          asOf: trendUserData.asOf,
        },
        document: {
          todayTotal: trendDocumentData.todayTotal,
          yesterdayTotal: trendDocumentData.yesterdayTotal,
          deltaPct: trendDocumentData.deltaPct,
          direction: trendDocumentData.direction,
          asOf: trendDocumentData.asOf,
        },
        error: {
          todayTotal: trendErrorData.todayTotal,
          yesterdayTotal: trendErrorData.yesterdayTotal,
          deltaPct: trendErrorData.deltaPct,
          direction: trendErrorData.direction,
          asOf: trendErrorData.asOf,
        },
      };
      setTrendData(normalziedTrendUserData);
    };

    fetchTrendData();
    fetchTotalData();
  }, []);

  const totalFieldMap = {
    user: 'totalUser',
    document: 'totalDocs',
    error: 'totalErrors',
  } as const;

  const anyConnected = connected?.user || connected?.document || connected?.error || false;
  const anyError = Boolean(errors?.user || errors?.document || errors?.error);

  const headerStatusPill = anyConnected ? (
    <StatusPill ok text="실시간" />
  ) : anyError ? (
    <StatusPill warn text="연결 오류" />
  ) : (
    <StatusPill text="대기" />
  );
  const LiveBadge = () => (
    <span
      className="inline-flex items-center gap-1
               px-1 py-[2px] text-[10px] font-semibold rounded-md
               bg-red-100 text-red-600 border border-red-200"
    >
      <span>LIVE</span>
      <span
        className="ml-1 px-1.5 py-[1px] rounded-md 
             bg-white/80 backdrop-blur-sm
             text-[10px] font-bold text-red-600 
             border border-red-200/70 shadow-[0_1px_2px_rgba(0,0,0,0.06)]
             tracking-tight tabular-nums"
      >
        {realtimeUserData?.result?.activeUserCount?.toLocaleString() ?? 0}
      </span>
    </span>
  );
  const renderCard = (
    key: keyof TrendGroup,
    title: string,
    icon: JSX.Element,
    totalLabel: string
  ) => {
    const current = currentData?.[key]?.data.accessUsers ?? 0;
    const trend = trendData?.[key];
    const total = totalData?.[key];
    const field = totalFieldMap[key];
    const totalCount = (total as Record<string, number | string | undefined>)?.[field] ?? 0;

    const deltaValue =
      trend?.deltaPct !== undefined ? Number((trend.deltaPct * 100).toFixed(2)) : 0;
    const direction = trend?.direction ?? 'flat';

    const IconArrow = direction === 'up' ? TrendingUp : direction === 'down' ? TrendingDown : null;
    const sign = deltaValue > 0 ? '+' : '';
    const colorClass =
      direction === 'up'
        ? 'text-emerald-600 bg-emerald-50 border-emerald-100'
        : direction === 'down'
          ? 'text-rose-600 bg-rose-50 border-rose-100'
          : 'text-slate-500 bg-slate-50 border-slate-100';

    const subtitle =
      key === 'user'
        ? '접속한 전체 사용자'
        : key === 'document'
          ? '업로드된 전체 문서'
          : '발생한 전체 오류';

    const asOf = trend?.asOf ?? total?.asOf;

    return (
      <article className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-sm transition-transform duration-150 hover:-translate-y-0.5 hover:border-slate-300">
        <header className="mb-6 flex items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            {icon}
            <div className="flex flex-col">
              <span className="text-lg font-medium text-gray-900">{title}</span>
              <span className="text-[11px] text-slate-400">{subtitle}</span>
            </div>
          </div>
          {key === 'user' && <LiveBadge />}
        </header>

        <div className="flex flex-1 flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-4xl font-semibold tracking-tight text-slate-900 tabular-nums leading-none">
                {current.toLocaleString()}
              </span>
            </div>

            <div className="flex flex-col items-end text-right">
              <span className="text-[11px] uppercase tracking-wide text-slate-400">
                {totalLabel}
              </span>
              <span className="text-base font-medium text-slate-600 tabular-nums">
                {totalCount.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-slate-400">전일 대비 변화</span>
            <div
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${colorClass}`}
            >
              {IconArrow && <IconArrow size={11} className="shrink-0" />}
              <span>
                {sign}
                {Math.abs(deltaValue).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {asOf && (
          <footer className="mt-3 border-t border-slate-100 pt-2">
            <span className="text-xs text-slate-400">
              <TimeRight ts={asOf} />
            </span>
          </footer>
        )}
      </article>
    );
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <header className="mb-4 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DatabaseZap size={18} className="text-[var(--color-hebees-blue)]" />
            <h3 className="text-xl font-semibold text-gray-900">오늘의 실시간 로그</h3>
          </div>

          <div>{headerStatusPill}</div>
        </div>
        <p className="text-sm text-gray-500">
          현재 접속, 문서 업로드, 오류 발생 현황을 한눈에 확인하세요.
        </p>
        <p></p>
      </header>

      <div className="mt-2 grid flex-1 grid-cols-1 gap-3 md:grid-cols-3">
        {renderCard(
          'user',
          '현재 사용자 수',
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-hebees-blue-bg)] shadow-sm">
            <Users size={20} className="text-[var(--color-hebees-blue)]" />
          </div>,
          '총 사용자'
        )}

        {renderCard(
          'document',
          '업로드 문서 수',
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-hebees-bg)] shadow-sm">
            <FileText size={20} className="text-[var(--color-hebees)]" />
          </div>,
          '총 문서'
        )}

        {renderCard(
          'error',
          '오류 발생 수',
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-50 shadow-sm">
            <TriangleAlert size={20} className="text-rose-500" />
          </div>,
          '총 오류'
        )}
      </div>
    </div>
  );
}
