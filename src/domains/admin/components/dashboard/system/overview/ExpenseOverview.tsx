import { Coins } from 'lucide-react';
import type { ReactNode } from 'react';
import Card from '@/shared/components/Card';
import {
  StatusPill,
  TimeRight,
} from '@/domains/admin/components/dashboard/system/overview/StatPrimitives';
import type { ExpenseEvent, ModelExpense } from '@/domains/admin/types/system.dashboard.types';

import ChatgptLogo from '@/assets/logos/chatgpt-logo.png';
import ClaudeLogo from '@/assets/logos/claude-logo.png';
import GeminiLogo from '@/assets/logos/gemini-logo.jpeg';
import Qwen3Logo from '@/assets/logos/qwen3-logo.jpeg';

const EXCHANGE_RATE_KRW_PER_USD = 1400;

function formatUsd(v?: number) {
  const n = typeof v === 'number' ? v : 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n);
}

function formatKrw(v?: number) {
  const n = typeof v === 'number' ? v : 0;
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(n);
}

type ModelBrandMeta = {
  label: string;
  icon: ReactNode;
  chipBg: string;
  chipText: string;
  accent: string;
};

function getModelBrandMeta(model: string): ModelBrandMeta {
  const lower = model.toLowerCase();

  if (lower.includes('gpt-4')) {
    return {
      label: 'GPT-4',
      icon: <img src={ChatgptLogo} alt="GPT-4" className="h-7 w-7 rounded-full" />,
      chipBg: 'bg-slate-900/5',
      chipText: 'text-slate-900',
      accent: 'stroke-slate-900',
    };
  }

  if (lower.includes('claude')) {
    return {
      label: 'Claude',
      icon: <img src={ClaudeLogo} alt="Claude" className="h-7 w-7 rounded-full" />,
      chipBg: 'bg-amber-50',
      chipText: 'text-amber-700',
      accent: 'stroke-amber-500',
    };
  }

  if (lower.includes('gemini')) {
    return {
      label: 'Gemini',
      icon: <img src={GeminiLogo} alt="Gemini" className="h-7 w-7 rounded-full" />,
      chipBg: 'bg-sky-50',
      chipText: 'text-sky-700',
      accent: 'stroke-sky-500',
    };
  }

  if (lower.includes('qwen')) {
    return {
      label: 'Qwen 3',
      icon: <img src={Qwen3Logo} alt="Qwen 3" className="h-7 w-7 rounded-full" />,
      chipBg: 'bg-violet-50',
      chipText: 'text-violet-700',
      accent: 'stroke-violet-500',
    };
  }

  const label = model.length > 0 ? model : '기타 모델';
  return {
    label: '기타 모델',
    icon: (
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-[10px] font-semibold text-white">
        {label.slice(0, 2).toUpperCase()}
      </div>
    ),
    chipBg: 'bg-slate-50',
    chipText: 'text-slate-700',
    accent: 'stroke-slate-400',
  };
}

interface ExpenseOverviewCardProps {
  expense: ExpenseEvent | null;
  connected?: boolean;
  error?: string | null;
}

export function ExpenseOverviewCard({ expense, connected, error }: ExpenseOverviewCardProps) {
  const status: ReactNode = connected ? (
    <StatusPill ok text="실시간" />
  ) : error ? (
    <StatusPill warn text="연결 오류" />
  ) : (
    <StatusPill text="대기" />
  );

  const grandUsd = expense?.grandPriceUsd ?? 0;
  const grandKrw = grandUsd * EXCHANGE_RATE_KRW_PER_USD;
  const krw = formatKrw(grandKrw);
  const symbol = krw.charAt(0);
  const number = krw.slice(1);

  const models: ModelExpense[] = expense?.models ?? [];
  const topModels = [...models].sort((a, b) => b.totalPriceUsd - a.totalPriceUsd).slice(0, 4);

  return (
    <Card
      title="예상 비용"
      subtitle="일일 모델 비용"
      icon={<Coins size={22} className="text-emerald-500" />}
      iconBg="bg-emerald-50"
      status={status}
      className="p-5 md:p-6 xl:p-7"
    >
      <div className="mb-4 flex flex-col gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-1.5">
            <span className="text-xs uppercase text-slate-400 mt-4">총 예상 비용</span>
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span className="text-[2.6rem] sm:text-[2.8rem] font-semibold leading-tight tracking-tight text-slate-900 tabular-nums">
                <span className="pr-[0.18em]">{symbol}</span>
                {number}
              </span>
              <span className="text-sm pl-1 text-slate-500 tabular-nums">
                {formatUsd(grandUsd)}
              </span>
            </div>
          </div>
          <TimeRight ts={expense?.timestamp} />
        </div>

        {grandUsd === 0 && (
          <span className="text-[12px] text-slate-400">
            아직 집계된 모델 비용 데이터가 많지 않습니다.
          </span>
        )}
      </div>

      {topModels.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-[12px] text-slate-500">
            <span>비용 상위 {topModels.length}개 모델</span>
            <span className="text-xs text-slate-400">
              환율 기준 {EXCHANGE_RATE_KRW_PER_USD.toLocaleString()}원 / 1$
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {topModels.map((m, index) => {
              const share = grandUsd > 0 ? (m.totalPriceUsd / grandUsd) * 100 : 0;
              const clampedShare = Math.max(0, Math.min(share, 100));
              const modelUsd = m.totalPriceUsd;
              const modelKrw = modelUsd * EXCHANGE_RATE_KRW_PER_USD;
              const brand = getModelBrandMeta(m.model);

              return (
                <article
                  key={m.model}
                  className="flex flex-col rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-sm transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-300"
                >
                  <header className="mb-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white shadow-[0_0_0_1px_rgba(15,23,42,0.05)]">
                        {brand.icon}
                      </div>

                      <div className="flex min-w-0 flex-col">
                        <span className="max-w-[170px] truncate text-[15px] font-semibold text-slate-900">
                          {brand.label}
                        </span>
                        <span className="max-w-[190px] truncate text-[13px] text-slate-500">
                          {m.model}
                        </span>
                      </div>
                    </div>

                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium ${brand.chipBg} ${brand.chipText}`}
                    >
                      TOP {index + 1}
                    </span>
                  </header>

                  <div className="mb-5 flex items-center justify-between gap-4">
                    <div className="flex flex-col gap-1">
                      <span className="text-[24px] font-bold leading-tight text-slate-900 tabular-nums">
                        {formatKrw(modelKrw)}
                      </span>
                      <span className="text-[13px] text-slate-400 tabular-nums">
                        {formatUsd(modelUsd)} / 하루
                      </span>
                    </div>

                    <div className="relative h-16 w-16">
                      <svg className="h-16 w-16 -rotate-90">
                        <circle
                          cx="50%"
                          cy="50%"
                          r={28}
                          className="stroke-slate-200"
                          strokeWidth={8}
                          fill="none"
                        />

                        <circle
                          cx="50%"
                          cy="50%"
                          r={28}
                          className={`${brand.accent} transition-all duration-300`}
                          strokeWidth={8}
                          fill="none"
                          strokeDasharray={2 * Math.PI * 28}
                          strokeDashoffset={2 * Math.PI * 28 * (1 - clampedShare / 100)}
                          strokeLinecap="round"
                        />
                      </svg>

                      <span className="absolute inset-0 flex items-center justify-center text-[14px] font-semibold text-slate-700">
                        {clampedShare.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <dl className="mt-auto space-y-2 text-sm">
                    <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-2">
                      <dt className="inline-flex items-center gap-2 text-slate-500">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span>입력 비용</span>
                      </dt>
                      <dd className="text-right">
                        <div className="text-[13px] font-medium text-slate-900 tabular-nums">
                          {formatKrw(m.inputPriceUsd * EXCHANGE_RATE_KRW_PER_USD)}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {formatUsd(m.inputPriceUsd)}
                        </div>
                      </dd>
                    </div>

                    <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-2">
                      <dt className="inline-flex items-center gap-2 text-slate-500">
                        <span className="h-2 w-2 rounded-full bg-sky-500" />
                        <span>출력 비용</span>
                      </dt>
                      <dd className="text-right">
                        <div className="text-[13px] font-medium text-slate-900 tabular-nums">
                          {formatKrw(m.outputPriceUsd * EXCHANGE_RATE_KRW_PER_USD)}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {formatUsd(m.outputPriceUsd)}
                        </div>
                      </dd>
                    </div>
                  </dl>
                </article>
              );
            })}
          </div>
        </div>
      ) : (
        <p className="mt-3 text-[12px] text-slate-400">비용 데이터가 없습니다.</p>
      )}
    </Card>
  );
}
