import { ChevronLeft, ChevronRight } from 'lucide-react';

type Props = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
};

export default function Pagination({ page, totalPages, onPageChange, className = '' }: Props) {
  const prev = () => onPageChange(Math.max(1, page - 1));
  const next = () => onPageChange(Math.min(totalPages, page + 1));

  return (
    <div className={`flex items-center justify-center gap-5 py-3 text-sm ${className}`}>
      <button
        onClick={prev}
        disabled={page === 1}
        className="flex items-center gap-2 text-gray-700 disabled:text-gray-300"
      >
        <ChevronLeft size={16} />
        <span className="hidden sm:inline">이전</span>
      </button>

      <div className="flex items-center gap-2 font-medium">
        {Array.from({ length: totalPages }).map((_, i) => {
          const pageNum = i + 1;
          return (
            <button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              className={
                page === pageNum ? 'font-semibold text-black' : 'text-gray-500 hover:text-black'
              }
            >
              {pageNum}
            </button>
          );
        })}
      </div>

      <button
        onClick={next}
        disabled={page === totalPages}
        className="flex items-center gap-2 text-gray-700 disabled:text-gray-300"
      >
        <span className="hidden sm:inline">다음</span>
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
