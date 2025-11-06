import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, GaugeCircle, Cpu } from 'lucide-react';
import Card from '@/shared/components/Card';
import Pagination from '@/shared/components/Pagination';
import type { errorList, errorItem } from '@/domains/admin/types/dashboard.types';
import { getErrorLogs } from '@/domains/admin/api/dashboard.api';

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
  const pageSize = 5;

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
      [...errors].sort(
        (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime()
      ),
    [errors]
  );
  const totalPages = Math.max(1, Math.ceil(sortedErrors.length / pageSize));
  console.log(sortedErrors);

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
    <Card title="발생한 오류 유형" subtitle="최근 24시간" className="p-4">
      <ul className="flex flex-col gap-2">
        {pageItems.map((err, i) => (
          <li
            key={`${err.chatRoomId}-${startIndex + i}`}
            className="flex items-center justify-between p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition"
          >
            <div className="flex items-center gap-3">
              {getIcon(err.errorType as 'SYSTEM' | '응답오류')}
              <div>
                <p className="text-sm font-semibold text-gray-800">{err.chatTitle}</p>
                <p className="text-xs text-gray-500">
                  {err.userType} • {timeAgo(new Date(err.occurredAt))}
                </p>
              </div>
            </div>

            <div
              className={`px-2 py-0.5 text-xs rounded-lg font-medium ${getBadgeStyle(
                err.errorType as 'SYSTEM' | '응답오류'
              )}`}
            >
              {err.errorType as 'SYSTEM' | '응답오류'}
            </div>
          </li>
        ))}
      </ul>
      <Pagination page={pageNum} totalPages={totalPages} onPageChange={setPageNum} />
    </Card>
  );
}
