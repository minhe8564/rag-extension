import { useEffect, useMemo, useState, type RefObject } from 'react';
import { ArrowDown } from 'lucide-react';
import clsx from 'clsx';

type Props = {
  containerRef: RefObject<HTMLElement>;
  watch?: number;
  smooth?: boolean;
  className?: string;
  bottomPadding?: number;
};

export default function ScrollToBottomButton({
  containerRef,
  watch = 0,
  smooth = true,
  className,
  bottomPadding = 0,
}: Props) {
  const [visible, setVisible] = useState(false);
  const [hasUnseen, setHasUnseen] = useState(false);

  const isAtBottom = () => {
    const el = containerRef.current;
    if (!el) return true;
    return el.scrollTop + el.clientHeight >= el.scrollHeight - 50;
  };

  const scrollToBottom = () => {
    const el = containerRef.current;
    if (!el) return;
    el.scrollTo({
      top: el.scrollHeight + bottomPadding,
      behavior: smooth ? 'smooth' : 'auto',
    });
  };

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onScroll = () => {
      const atBottom = isAtBottom();
      setVisible(!atBottom);
      if (atBottom) setHasUnseen(false);
    };

    onScroll();
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [containerRef]);

  const w = useMemo(() => watch, [watch]);
  useEffect(() => {
    if (!containerRef.current) return;
    if (!isAtBottom()) setHasUnseen(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [w]);

  if (!visible) return null;

  return (
    <button
      onClick={() => {
        scrollToBottom();
        setHasUnseen(false);
      }}
      className={clsx(
        'inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2 text-sm shadow-lg',
        'text-gray-700 hover:bg-gray-50 transition',
        'focus:outline-none focus-visible:outline-none',
        className
      )}
    >
      {hasUnseen && (
        <span className="relative mr-1 inline-flex h-2.5 w-2.5 items-center justify-center">
          <span className="absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60 animate-ping"></span>
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
        </span>
      )}
      <ArrowDown size={16} />
      최신 메시지
    </button>
  );
}
