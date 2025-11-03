type SliderProps = {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  className?: string;
};

export function Slider({ value, min, max, step = 1, onChange, className = '' }: SliderProps) {
  const percent = ((value - min) / (max - min)) * 100;

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      const clamped = Math.min(max, Math.max(min, val));
      onChange(clamped);
    }
  };

  return (
    <div className="w-full flex items-center gap-3">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{
          background: `linear-gradient(
            to right,
            var(--color-hebees) ${percent}%,
            var(--color-hebees-bg) ${percent}%
          )`,
        }}
        className={`w-full h-2 rounded-full appearance-none cursor-pointer ${className} slider-hebees`}
      />

      <input
        type="number"
        value={value}
        onChange={handleInput}
        min={min}
        max={max}
        step={step}
        className="w-14 text-right text-base font-medium text-gray-700 border-none rounded-md px-1 py-0.5 focus:outline-none focus:ring-[var(--color-white)] focus:border-transparent"
      />
    </div>
  );
}
