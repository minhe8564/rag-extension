import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, GaugeCircle, Cpu } from 'lucide-react';
import Pagination from '@/shared/components/Pagination';
import type { errorList, errorItem } from '@/domains/admin/types/rag.dashboard.types';
import { getErrorLogs } from '@/domains/admin/api/rag.dashboard.api';
import { ShieldAlert } from 'lucide-react';

// 시간 경과 계산 함수
function timeAgo(date: Date) {
  const diff = Math.floor((Date.now() - date.getTime()) / 60000); // 분 단위
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  const hours = Math.floor(diff / 60);
  return `${hours}시간 전`;
}

export default function ErrorTypes() {
  const [_data, setData] = useState<errorList | null>(null);
  const [errors, setErrors] = useState<errorItem[]>([]);
  const [pageNum, setPageNum] = useState(1);
  const pageSize = 4;

  useEffect(() => {
    const fetchData = async () => {
      const result = await getErrorLogs();
      setData(result);
      setErrors(result.errors);
    };
    fetchData();
  }, []);

  const sortedErrors = useMemo(
    () =>
      [...errors].sort((a, b) => new Date(b.occuredAt).getTime() - new Date(a.occuredAt).getTime()),
    [errors]
  );
  const totalPages = Math.max(1, Math.ceil(sortedErrors.length / pageSize));

  const getIcon = (type: 'SYSTEM' | '응답오류') => {
    switch (type) {
      case 'SYSTEM':
        return <Cpu className="text-orange-500" size={18} />;
      case '응답오류':
        return <AlertTriangle className="text-red-500" size={18} />;
      default:
        return <GaugeCircle className="text-gray-400" size={18} />;
    }
  };

  const getBadgeStyle = (type: 'SYSTEM' | '응답오류') => {
    if (type === 'SYSTEM') return 'bg-blue-100 text-blue-700 border border-blue-300';
    if (type === '응답오류') return 'bg-red-100 text-red-700 border border-red-300';
    return 'bg-gray-100 text-gray-700 border border-gray-300';
  };

  const startIndex = (pageNum - 1) * pageSize;
  const pageItems = sortedErrors.slice(startIndex, startIndex + pageSize);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <ShieldAlert size={18} className="text-amber-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">발생한 오류 유형</h3>
      </div>
      <p className="mt-0.5 mb-4 text-sm text-gray-500">최근 24시간</p>

      <ul className="flex flex-col gap-2 mb-1 min-h-[220px] flex-1 justify-center items-center">
        {pageItems.length === 0 ? (
          <div className="text-gray-400 text-sm py-10">
            최근 24시간 동안 발생한 오류가 없습니다.
          </div>
        ) : (
          pageItems.map((err, i) => (
            <li
              key={`${err.chatRoomId}-${startIndex + i}`}
              className="flex items-center justify-between p-4 mb-2 rounded-xl
                 bg-gray-50 hover:bg-gray-100 transition-colors w-full"
            >
              <div className="flex items-center gap-4">
                {getIcon(err.errorType as 'SYSTEM' | '응답오류')}

                <div className="flex flex-col">
                  <p className="text-sm font-semibold text-gray-900">{err.chatTitle}</p>
                  <p className="text-xs text-gray-500 mt-[2px]">
                    {err.userType} • {timeAgo(new Date(err.occuredAt))}
                  </p>
                </div>
              </div>

              <div
                className={`px-2.5 py-1 text-xs rounded-lg font-medium 
            whitespace-nowrap ${getBadgeStyle(err.errorType as 'SYSTEM' | '응답오류')}`}
              >
                {err.errorType}
              </div>
            </li>
          ))
        )}
      </ul>
      <div className="mt-auto">
        <Pagination pageNum={pageNum} totalPages={totalPages} onPageChange={setPageNum} />
      </div>
    </div>
  );
}
