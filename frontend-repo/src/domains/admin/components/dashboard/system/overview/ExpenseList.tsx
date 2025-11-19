export type ModelExpense = {
  model: string;
  inputPriceUsd: number;
  outputPriceUsd: number;
  totalPriceUsd: number;
};

function formatUsd(v?: number) {
  const n = typeof v === 'number' ? v : 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 3,
  }).format(n);
}

function percent(n: number, total: number) {
  return total === 0 ? 0 : Math.round((n / total) * 100);
}

const COLORS = [
  {
    tone: 'sky',
    main: 'bg-sky-500',
    soft: 'bg-sky-50',
    border: 'border-sky-100',
    textSoft: 'text-sky-800',
  },
  {
    tone: 'violet',
    main: 'bg-violet-500',
    soft: 'bg-violet-50',
    border: 'border-violet-100',
    textSoft: 'text-violet-800',
  },
  {
    tone: 'emerald',
    main: 'bg-emerald-500',
    soft: 'bg-emerald-50',
    border: 'border-emerald-100',
    textSoft: 'text-emerald-800',
  },
];

function colorForIndex(i: number) {
  return COLORS[i % COLORS.length];
}

function ModelChip({ model, c }: { model: string; c: ReturnType<typeof colorForIndex> }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-[2px] text-[11px] font-semibold max-w-[180px] overflow-hidden ${c.soft} ${c.border} ${c.textSoft}`}
      title={model}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.main}`} />
      <span className="truncate">{model}</span>
    </span>
  );
}

function InOut({ input, output }: { input: number; output: number }) {
  return (
    <div className="flex items-center gap-4 text-[11px] text-gray-600">
      <span className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-500" />
        In <span className="font-medium text-gray-800">{formatUsd(input)}</span>
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
        Out <span className="font-medium text-gray-800">{formatUsd(output)}</span>
      </span>
    </div>
  );
}

function PercentPill({ p, c }: { p: number; c: ReturnType<typeof colorForIndex> }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-[3px] text-[11px] font-medium ${c.soft} ${c.textSoft}`}
    >
      {p}% 사용
    </span>
  );
}

function Row({ m, total, index }: { m: ModelExpense; total: number; index: number }) {
  const c = colorForIndex(index);
  const p = percent(m.totalPriceUsd, total);

  return (
    <div className="relative rounded-xl border border-gray-100 bg-gray-50">
      <div className="grid grid-cols-[1fr_auto] gap-3 pl-4 pr-4 py-4">
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-2">
            <ModelChip model={m.model} c={c} />
          </div>
          <InOut input={m.inputPriceUsd} output={m.outputPriceUsd} />
        </div>

        <div className="flex flex-col items-end gap-2">
          <span className="text-base font-semibold text-gray-900 tabular-nums leading-none">
            {formatUsd(m.totalPriceUsd)}
          </span>
          <PercentPill p={p} c={c} />
        </div>
      </div>
    </div>
  );
}

export function ExpenseList({
  models,
  grand,
  gap = 8,
}: {
  models: ModelExpense[];
  grand?: number;
  gap?: number;
}) {
  const total = grand ?? models.reduce((s, v) => s + v.totalPriceUsd, 0);
  const sorted = [...models].sort((a, b) => b.totalPriceUsd - a.totalPriceUsd);

  return (
    <div className="mt-6 max-h-[120px] overflow-y-auto " style={{ display: 'grid', gap }}>
      {sorted.map((m, i) => (
        <Row key={m.model} m={m} total={total} index={i} />
      ))}
    </div>
  );
}
