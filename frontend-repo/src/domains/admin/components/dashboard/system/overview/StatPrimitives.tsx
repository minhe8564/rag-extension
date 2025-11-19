import type { ReactNode } from 'react';

export function ProgressBar({
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
      <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
        <div
          className={`h-2 rounded-full ${color} transition-all duration-500 ease-out`}
          style={{ width: `${v}%` }}
        />
      </div>

      {showLabel && (
        <div className="mt-1 text-[11px] text-gray-500 text-right">{v.toFixed(0)}%</div>
      )}
    </div>
  );
}

export function StatusPill({ ok, warn, text }: { ok?: boolean; warn?: boolean; text: string }) {
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

export function HintPair({
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
    <div className="mt-4 grid grid-cols-2 gap-6 text-sm">
      <div className="rounded-md border border-gray-100 bg-gray-50 px-3 py-2">
        <div className="text-[11px] text-gray-500">{leftLabel}</div>
        <div className="font-medium text-gray-800">{leftValue}</div>
      </div>
      <div className="rounded-md border border-gray-100 bg-gray-50 px-3 py-2">
        <div className="text-[11px] text-gray-500">{rightLabel}</div>
        <div className="font-medium text-gray-800">{rightValue}</div>
      </div>
    </div>
  );
}

export function StatCardContent({
  value,
  suffix,
  footer,
  barValue,
  barColor = 'bg-emerald-500',
  topLeft, // timestamp
  topRight, // status tag etc.
  hints,
  customContent,
}: {
  value: string | number;
  suffix?: string;
  footer?: string;
  barValue?: number;
  barColor?: string;
  topLeft?: ReactNode;
  topRight?: ReactNode;
  hints?: { leftLabel: string; leftValue: string; rightLabel: string; rightValue: string };
  customContent?: ReactNode;
}) {
  return (
    <>
      <div className="flex items-center justify-between mb-1">
        <div className="text-[11px] text-gray-500 self-end leading-none mt-1">{topLeft}</div>

        <div className="text-3xl font-semibold text-gray-900 text-right">
          {value}
          {suffix && <span className="ml-1 text-lg font-medium text-gray-500">{suffix}</span>}
        </div>
      </div>

      {topRight && <div className="flex justify-end mb-1">{topRight}</div>}

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

      {customContent}

      {footer && <div className="mt-3 text-xs text-gray-500 text-right">{footer}</div>}
    </>
  );
}

export function TimeRight({ ts }: { ts?: string }) {
  if (!ts) return null;
  return (
    <span className="text-[11px] text-gray-500">
      {new Date(ts).toLocaleTimeString('ko-KR', { hour12: false })}
    </span>
  );
}
