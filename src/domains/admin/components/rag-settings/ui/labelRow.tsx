type LabelRowProps = {
  label: string;
  hint?: string;
  className?: string;
};

export function LabelRow({ label, hint, className = '' }: LabelRowProps) {
  return (
    <div className={`mb-2 flex items-center justify-between ${className}`}>
      <div className="min-w-0">
        <div className="text-base font-bold text-gray-700">{label}</div>
        {hint && <div className="text-sm my-1 text-gray-400 whitespace-pre-line">{hint}</div>}
      </div>
    </div>
  );
}
