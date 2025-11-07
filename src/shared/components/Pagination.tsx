import { ChevronLeft, ChevronRight } from 'lucide-react';

type Props = {
  pageNum: number;
  totalPages: number;
  onPageChange: (pageNum: number) => void;
  className?: string;
  hasPrev?: boolean;
  hasNext?: boolean;
  isLoading?: boolean;
};

export default function Pagination({
  pageNum,
  totalPages,
  onPageChange,
  className = '',
  hasPrev,
  hasNext,
  isLoading = false,
}: Props) {
  const canPrev = hasPrev ?? pageNum > 1;
  const canNext = hasNext ?? pageNum < totalPages;

  const goPage = (p: number) => {
    if (isLoading) return;
    onPageChange(p);
  };

  const prev = () => {
    if (!canPrev || isLoading) return;
    goPage(pageNum - 1);
  };

  const next = () => {
    if (!canNext || isLoading) return;
    const target = hasNext !== undefined ? pageNum + 1 : Math.min(totalPages, pageNum + 1);
    goPage(target);
  };

  return (
    <div className={`flex items-center justify-center gap-5 py-3 text-sm ${className}`}>
      <button
        type="button"
        onClick={prev}
        disabled={!canPrev || isLoading}
        className="flex items-center gap-2 text-gray-700 disabled:text-gray-300"
      >
        <ChevronLeft size={16} />
        <span className="hidden sm:inline">이전</span>
      </button>

      <div className="flex items-center gap-2 font-medium">
        {Array.from({ length: Math.max(1, totalPages) }).map((_, i) => {
          const n = i + 1;
          return (
            <button
              type="button"
              key={n}
              onClick={() => goPage(n)}
              disabled={isLoading}
              className={
                pageNum === n
                  ? 'font-semibold text-black'
                  : 'text-gray-500 hover:text-black disabled:text-gray-300'
              }
            >
              {n}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={next}
        disabled={!canNext || isLoading}
        className="flex items-center gap-2 text-gray-700 disabled:text-gray-300"
      >
        <span className="hidden sm:inline">다음</span>
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
