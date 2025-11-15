import { useState, useRef, useLayoutEffect } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  side?: 'top' | 'bottom' | 'right';
  shiftX?: number;
  shiftY?: number;
  offset?: number;
  portal?: boolean;
}

export default function Tooltip({
  content,
  children,
  side = 'top',
  shiftX = 0,
  shiftY = 0,
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
      let top = 0;
      let left = 0;

      if (side === 'top') {
        top = r.top - offset + shiftY;
        left = r.left + r.width / 2 + shiftX;
      } else if (side === 'bottom') {
        top = r.bottom + offset + shiftY;
        left = r.left + r.width / 2 + shiftX;
      } else if (side === 'right') {
        top = r.top + r.height / 2 + shiftY;
        left = r.right + offset + shiftX;
      }

      setPos({ top, left });
    };

    calc();
    window.addEventListener('scroll', calc, true);
    window.addEventListener('resize', calc);
    return () => {
      window.removeEventListener('scroll', calc, true);
      window.removeEventListener('resize', calc);
    };
  }, [portal, open, side, offset, shiftX, shiftY]);

  const tooltipNode = (
    <div
      role="tooltip"
      className="z-[9999] whitespace-nowrap rounded-md bg-[var(--overlay-90)] px-2 py-1 text-xs text-white shadow-md transition-opacity duration-100 pointer-events-none"
      style={
        portal
          ? {
              position: 'fixed',
              top: pos.top,
              left: pos.left,
              transform:
                side === 'top'
                  ? 'translate(-50%, -100%)'
                  : side === 'bottom'
                    ? 'translate(-50%, 0)'
                    : 'translate(0, -50%)',
            }
          : side === 'right'
            ? {
                position: 'absolute',
                top: `calc(50% + ${shiftY}px)`,
                left: `calc(100% + ${offset}px + ${shiftX}px)`,
                transform: 'translateY(-50%)',
              }
            : {
                position: 'absolute',
                top:
                  side === 'top'
                    ? `calc(-${offset + 28}px + ${shiftY}px)`
                    : `calc(100% + ${offset}px + ${shiftY}px)`,
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
    >
      {children}
      {open && (portal ? createPortal(tooltipNode, document.body) : tooltipNode)}
    </div>
  );
}
