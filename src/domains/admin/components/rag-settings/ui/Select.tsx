import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';

type Option = { label: string; value: string; desc?: string };

type SelectMenuProps = {
  value?: string;
  onChange: (v: string) => void;
  options: Option[];
  placeholder?: string;
  className?: string;
  disabled?: boolean;
};

export function Select({
  value,
  onChange,
  options,
  placeholder = '선택하세요',
  className = '',
  disabled,
}: SelectMenuProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => options.find(o => o.value === value), [options, value]);

  // 외부 클릭 닫기
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={
          'flex w-full items-center justify-between rounded-lg border px-3 py-2 text-base outline-none transition disabled:cursor-not-allowed disabled:bg-gray-100'
        }
      >
        <span className={selected ? 'text-gray-900' : 'text-gray-400'}>
          {selected?.label ?? placeholder}
        </span>

        <ChevronDown
          size={16}
          className={`text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          role="listbox"
          tabIndex={-1}
          className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border bg-white p-2 shadow-xl"
        >
          <ul className="max-h-72 overflow-auto">
            {options.map(o => {
              const isSelected = o.value === value;
              return (
                <li
                  key={o.value}
                  role="option"
                  aria-selected={isSelected}
                  className={[
                    'cursor-pointer rounded-md px-3 py-2 transition',
                    isSelected ? 'bg-gray-100' : 'bg-white',
                  ].join(' ')}
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-base font-medium text-gray-900">{o.label}</div>
                      {o.desc && (
                        <div className="mt-1 text-xs leading-snug text-gray-500">{o.desc}</div>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
