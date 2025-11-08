import clsx from 'clsx';

type TooltipProps = {
  id: string;
  title: string;
  description?: string;
  note?: string;
  className?: string;
};

export function PipelineTooltip({ id, title, description, note, className }: TooltipProps) {
  if (!description && !note) return null;

  return (
    <div
      id={id}
      role="tooltip"
      className={clsx(
        'pointer-events-none absolute left-1/2 top-full mt-3 -translate-x-1/2',
        'z-50 w-full min-w-[200px] max-w-[480px] rounded-xl bg-[var(--overlay-90)] text-white',
        'opacity-0 translate-y-1 scale-[0.99] transition-all duration-150',
        'group-hover:opacity-100 group-hover:translate-y-0 group-hover:scale-100',
        className
      )}
    >
      <div className="px-4 py-3.5">
        <div className="text-base font-semibold text-white">{title}</div>
        {description && (
          <p className="mt-0.5 text-xs leading-5 text-white/80 whitespace-pre-line">
            {description}
          </p>
        )}
        {note && (
          <div className="mt-3 rounded-md border border-white/5 bg-white/5 px-3 py-2 text-[12px] font-semibold text-white/80">
            {note}
          </div>
        )}
      </div>
    </div>
  );
}
