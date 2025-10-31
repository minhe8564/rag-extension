type CardProps = {
  title: string;
  tip?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
};

export default function Card({ title, tip, subtitle, children, className = '' }: CardProps) {
  return (
    <section className={`rounded-2xl border bg-white p-8 shadow-sm ${className}`}>
      <header className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">{title}</h3>
        {tip && (
          <p className="mt-4 inline-flex items-center gap-2 rounded-md bg-[var(--color-hebees-bg)] px-3 py-1 text-sm font-normal text-[var(--color-hebees)]">
            <span className="font-bold">TIP</span>
            {tip}
          </p>
        )}

        {subtitle && <p className="mt-2 text-sm text-gray-500">{subtitle}</p>}
      </header>
      {children}
    </section>
  );
}
