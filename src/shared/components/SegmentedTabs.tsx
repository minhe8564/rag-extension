import { useId, useMemo } from 'react';
import type { PropsWithChildren } from 'react';
import clsx from 'clsx';

type TabKey = string;

export type SegmentedTab = {
  key: TabKey;
  label: string;
  icon?: React.ReactNode;
};

type SegmentedTabsProps = {
  tabs: SegmentedTab[];
  value: TabKey;
  onChange: (key: TabKey) => void;
  className?: string;
  brand?: 'retina' | 'hebees';
};

export default function SegmentedTabs({
  tabs,
  value,
  onChange,
  className,
  brand = 'retina',
}: PropsWithChildren<SegmentedTabsProps>) {
  const activeIndex = useMemo(() => tabs.findIndex((t) => t.key === value), [tabs, value]);
  const id = useId();

  return (
    <div
      className={clsx(
        'inline-flex w-full max-w-[560px] select-none rounded-2xl bg-gray-100 p-1',
        'relative shadow-[inset_0_0_0_1px_rgba(0,0,0,0.04)]',
        className
      )}
      role="tablist"
    >
      <div
        className={clsx(
          'absolute top-1 bottom-1 rounded-xl transition-all duration-200',
          brand === 'retina' ? 'bg-white' : 'bg-white'
        )}
        style={{
          left: `calc(${activeIndex} * (100% / ${tabs.length}) + 4px)`,
          width: `calc(100% / ${tabs.length} - 8px)`,
          boxShadow: '0 1px 6px rgba(0,0,0,0.06)',
        }}
      />
      {tabs.map((t) => {
        const active = t.key === value;
        return (
          <button
            key={t.key}
            id={`${id}-${t.key}`}
            role="tab"
            aria-selected={active}
            aria-controls={`${id}-${t.key}-panel`}
            onClick={() => onChange(t.key)}
            className={clsx(
              'relative z-[1] flex-1 rounded-xl px-4 py-2 text-sm font-medium',
              'transition-colors duration-150',
              active ? 'text-black' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            <span className="inline-flex items-center justify-center gap-2">
              {t.icon}
              {t.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
