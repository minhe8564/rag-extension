import { useState, useRef } from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  side?: 'top' | 'bottom';
  shiftX?: number;
  offset?: number;
}

export default function Tooltip({
  content,
  children,
  side = 'top',
  shiftX = 0,
  offset = 8,
}: TooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={ref}
      className="relative inline-flex items-center"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}

      {open && (
        <div
          className="absolute z-50 whitespace-nowrap rounded-md bg-[var(--overlay-90)] px-2 py-1 text-xs text-white shadow-md transition-opacity duration-100"
          style={{
            top: side === 'top' ? `-${offset + 28}px` : `calc(100% + ${offset}px)`,
            left: '50%',
            transform: `translateX(calc(-50% + ${shiftX}px))`,
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
}
