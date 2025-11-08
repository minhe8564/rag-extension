import type { ReactNode } from 'react';

type CardProps = {
  title?: string;
  icon?: ReactNode;
  iconBg?: string;
  tip?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
};

export default function Card({
  title,
  icon,
  iconBg = 'bg-[var(--color-hebees-bg)]',
  tip,
  subtitle,
  children,
  className = '',
}: CardProps) {
  return (
    <section className={`rounded-2xl border bg-white p-8 shadow-sm ${className}`}>
      {title && (
        <div className="mb-2">
          <div className="flex items-start gap-3">
            {icon && (
              <div className={`w-11 h-11 flex items-center justify-center rounded-xl ${iconBg}`}>
                {icon}
              </div>
            )}

            <div className="flex flex-col justify-center">
              <h3 className="font-semibold text-gray-900">{title}</h3>
              {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
            </div>
          </div>

          {tip && (
            <p className="mt-2 inline-flex items-center gap-2 rounded-md bg-[var(--color-hebees-bg)] px-3 py-1 text-sm font-normal text-[var(--color-hebees)]">
              <span className="font-bold">TIP</span>
              {tip}
            </p>
          )}
        </div>
      )}

      {children}
    </section>
  );
}
