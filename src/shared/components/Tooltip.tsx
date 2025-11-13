import { useState, useRef, useLayoutEffect } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  side?: 'top' | 'bottom';
  shiftX?: number;
  offset?: number;
  portal?: boolean;
}

export default function Tooltip({
  content,
  children,
  side = 'top',
  shiftX = 0,
  offset = 8,
  portal = false,
}: TooltipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });

  useLayoutEffect(() => {
    if (!portal || !open || !ref.current) return;

    const calc = () => {
      const r = ref.current!.getBoundingClientRect();
      const top = side === 'top' ? r.top - offset : r.bottom + offset;
      const left = r.left + r.width / 2 + shiftX;
      setPos({ top, left });
    };

    calc();
    window.addEventListener('scroll', calc, true);
    window.addEventListener('resize', calc);
    return () => {
      window.removeEventListener('scroll', calc, true);
      window.removeEventListener('resize', calc);
    };
  }, [portal, open, side, offset, shiftX]);

  const tooltipNode = (
    <div
      role="tooltip"
      className="z-[1000] whitespace-nowrap rounded-md bg-[var(--overlay-90)] px-2 py-1 text-xs text-white shadow-md transition-opacity duration-100 pointer-events-none"
      style={
        portal
          ? {
              position: 'fixed',
              top: pos.top,
              left: pos.left,
              transform: side === 'top' ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
            }
          : {
              position: 'absolute',
              top: side === 'top' ? `-${offset + 28}px` : `calc(100% + ${offset}px)`,
              left: '50%',
              transform: `translateX(calc(-50% + ${shiftX}px))`,
            }
      }
    >
      {content}
    </div>
  );

  return (
    <div
      ref={ref}
      className="relative inline-flex items-center"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      aria-haspopup="true"
      aria-expanded={open}
    >
      {children}
      {open && (portal ? createPortal(tooltipNode, document.body) : tooltipNode)}
    </div>
  );
}
