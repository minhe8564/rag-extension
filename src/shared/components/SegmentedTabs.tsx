import clsx from 'clsx';

export type SegmentedTab<K extends string> = {
  key: K;
  label: string;
  icon?: React.ReactNode;
};

interface SegmentedTabsProps<K extends string> {
  tabs: SegmentedTab<K>[];
  value: K;
  onChange: (key: K) => void;
  className?: string;
  brand?: 'retina' | 'hebees';
  fullWidth?: boolean;
  durationMs?: number;
}

export default function SegmentedTabs<K extends string>({
  tabs,
  value,
  onChange,
  className,
  brand = 'retina',
  fullWidth = true,
  durationMs = 280,
}: SegmentedTabsProps<K>) {
  const activeIdx = Math.max(
    0,
    tabs.findIndex((t) => t.key === value)
  );
  const colorVar = brand === 'hebees' ? 'var(--color-hebees)' : 'var(--color-retina)';

  return (
    <div
      className={clsx(
        'relative select-none border-b border-gray-200',
        fullWidth ? 'w-full' : 'inline-flex',
        className
      )}
      role="tablist"
      style={{ ['--color-active' as string]: colorVar }}
    >
      <div
        className="pointer-events-none absolute bottom-0 h-[2px] w-[var(--tab-w)]
                   will-change-transform transition-transform 
                   ease-[cubic-bezier(0.2,0.8,0.2,1)]"
        style={{
          ['--tab-w' as string]: `calc(100% / ${tabs.length})`,
          transform: `translateX(${activeIdx * 100}%)`,
          backgroundColor: `var(--color-active)`,
          transitionDuration: `${durationMs}ms`,
        }}
      />

      <div className="relative flex w-full">
        {tabs.map((t) => {
          const active = t.key === value;
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              onClick={() => onChange(t.key)}
              className={clsx(
                'flex-1 px-5 py-2.5 text-[16px] md:text-[17px]',
                'font-semibold transition-colors duration-200',
                active ? 'text-black' : 'text-gray-600 hover:text-[var(--color-active)]'
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
    </div>
  );
}
