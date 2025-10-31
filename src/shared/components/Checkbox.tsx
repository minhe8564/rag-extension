import React, { useEffect, useRef } from 'react';
import { Check, Minus } from 'lucide-react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  checked: boolean;
  indeterminate?: boolean;
}

export default function Checkbox({ checked, indeterminate, ...props }: CheckboxProps) {
  const ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.indeterminate = Boolean(indeterminate);
    }
  }, [indeterminate]);

  return (
    <label className="inline-flex items-center cursor-pointer select-none">
      <input ref={ref} type="checkbox" checked={checked} {...props} className="peer sr-only" />
      <span
        className={`
    h-4 w-4 rounded-md border flex items-center justify-center 
    transition-all border-gray-300 
    peer-checked:bg-[var(--color-hebees)]/10 
    peer-checked:border-[1.5px] 
    peer-checked:border-[var(--color-hebees)]
  `}
      >
        {indeterminate ? (
          <Minus className="h-3 w-3 text-[var(--color-hebees)]" strokeWidth={3} />
        ) : checked ? (
          <Check className="h-3 w-3 text-[var(--color-hebees)]" strokeWidth={3} />
        ) : null}
      </span>
    </label>
  );
}
