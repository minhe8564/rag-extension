import React from 'react';
import clsx from 'clsx';
import { PipelineTooltip } from '@/shared/components/rag-pipeline/PipelineTooltip';

export type FlowStepId =
  | 'extract'
  | 'chunking'
  | 'embedding'
  | 'query-embed'
  | 'searching'
  | 'reranker'
  | 'prompting'
  | 'generation';

export type FlowStep = {
  id: FlowStepId;
  label: string;
  sublabel?: string;
  icon: React.ReactNode;
  durationMs?: number;
  description?: string;
  tooltipNote?: string;
};

type Props = {
  steps: FlowStep[];
  activeId?: FlowStepId;
  onStepClick?: (id: FlowStepId) => void;
  className?: string;
};

export default function PipelineFlow({ steps, activeId, onStepClick, className }: Props) {
  const activeIndex = Math.max(0, activeId ? steps.findIndex((s) => s.id === activeId) : 0);
  const cols = steps.length;
  const percent = cols > 1 ? (activeIndex / (cols - 1)) * 100 : 0;

  return (
    <div className={clsx('relative w-full select-none', className)}>
      <div className="absolute top-12 left-8 right-8 h-[6px] rounded-full bg-gray-200" />

      <div
        className="absolute top-12 h-[6px] rounded-full transition-all duration-500"
        style={{
          width: `calc(${percent}% )`,
          background:
            'var(--color-hebees-gradient, linear-gradient(90deg,#BE7DB1 10%,#81BAFF 100%))',
          boxShadow: '0 0 0 1px rgba(0,0,0,0.02)',
        }}
      />

      <div
        className="grid gap-12 px-6 pt-4"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
      >
        {steps.map((s, i) => {
          const isActive = s.id === activeId;
          const isCompleted = i < activeIndex;
          const isPending = i > activeIndex;
          const ttId = `flow-tt-${s.id}`;

          return (
            <button
              key={s.id}
              type="button"
              onClick={() => onStepClick?.(s.id)}
              aria-current={isActive ? 'step' : undefined}
              aria-describedby={s.description || s.tooltipNote ? ttId : undefined}
              title={s.label}
              className={clsx(
                'group relative flex flex-col items-center text-center overflow-visible',
                'rounded-xl px-[2px] py-[2px] transition-all duration-200',
                isActive
                  ? 'bg-[linear-gradient(90deg,#BE7DB1_0%,#81BAFF_100%)] shadow-[0_0_8px_rgba(190,125,177,0.25)]'
                  : 'bg-transparent hover:scale-[1.02]'
              )}
            >
              <div
                className={clsx(
                  'w-full h-full rounded-xl bg-white border transition-all duration-200',
                  isActive ? 'border-transparent' : 'border-gray-200 group-hover:border-gray-300'
                )}
              >
                <div className="flex flex-col items-center text-center px-3 py-5">
                  <div className="absolute inset-x-0 -top-6 flex items-center justify-center">
                    <span className="relative inline-flex h-2.5 w-2.5 items-center justify-center">
                      {isActive && (
                        <span className="absolute inline-flex h-full w-full rounded-full bg-[#BE7DB1] opacity-50 animate-ping"></span>
                      )}
                      <span
                        className={clsx(
                          'relative inline-flex h-2.5 w-2.5 rounded-full transition-all',
                          isPending && 'bg-gray-300',
                          isCompleted && 'bg-[#BE7DB1]',
                          isActive && 'animate-popbubble'
                        )}
                        style={
                          isActive
                            ? {
                                background: 'linear-gradient(90deg,#BE7DB1 0%,#81BAFF 100%)',
                                boxShadow: '0 0 0 4px rgba(190,125,177,0.12)',
                              }
                            : undefined
                        }
                      />
                    </span>
                  </div>

                  <div
                    className={clsx(
                      'flex h-16 w-16 items-center justify-center rounded-xl transition-all duration-200 group-hover:scale-110',
                      isActive ? 'shadow-sm' : 'shadow-[inset_0_0_0_1px_rgba(0,0,0,0.04)]'
                    )}
                    style={{
                      background: isActive
                        ? 'linear-gradient(180deg, rgba(190,125,177,0.12) 0%, rgba(129,186,255,0.16) 100%)'
                        : '#F7F8FA',
                    }}
                  >
                    {s.icon}
                  </div>

                  <div
                    className={clsx(
                      'mt-3 text-sm font-semibold tracking-[0.01em]',
                      isActive ? 'text-gray-900' : 'text-gray-800'
                    )}
                  >
                    {s.label}
                  </div>
                  {s.sublabel && <div className="text-[11px] text-gray-500">{s.sublabel}</div>}
                  {typeof s.durationMs === 'number' && (
                    <div className="mt-2 text-xs text-gray-500">{s.durationMs}ms</div>
                  )}

                  <PipelineTooltip
                    id={ttId}
                    title={s.label}
                    description={s.description}
                    note={s.tooltipNote}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
