import { useEffect, useMemo, useState } from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import Pagination from '@/shared/components/Pagination';
import { getChatRooms } from '@/domains/admin/api/rag.dashboard.api';
import type {
  createdChatrooms,
  chatroomTimeframe,
} from '@/domains/admin/types/rag.dashboard.types';
import { Activity } from 'lucide-react';
import clsx from 'clsx';

// 시간 경과 계산 함수
function timeAgo(date: Date) {
  const diff = Math.floor((Date.now() - date.getTime()) / 60000); // 분 단위
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  const hours = Math.floor(diff / 60);
  return `${hours}시간 전`;
}

export default function ChatRoom() {
  const [_data, setData] = useState<createdChatrooms | null>(null);
  const [chatrooms, setChatrooms] = useState<createdChatrooms['chatrooms']>([]);
  const [_timeframe, setTimeframe] = useState<chatroomTimeframe | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getChatRooms();
      setData(result);
      setChatrooms(result.chatrooms);
      setTimeframe(result.timeframe);

      console.log(result);
    };
    fetchData();
  }, []);

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 4;
  const sortedRooms = useMemo(
    () =>
      [...chatrooms].sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      ),
    [chatrooms]
  );
  const totalPages = Math.max(1, Math.ceil(sortedRooms.length / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const pageItems = sortedRooms.slice(startIndex, startIndex + pageSize);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <Activity size={18} className="text-purple-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">생성된 채팅방</h3>
      </div>
      <p className="mt-0.5 mb-4 text-sm text-gray-500">최근 활동 기준</p>
      <ul className="flex flex-col gap-3">
        {pageItems.map((room, i) => (
          <li
            key={`${room.chatRoomId}-${startIndex + i}`}
            className="flex items-center justify-between p-4 mb-2 rounded-xl
               bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div
                className="flex items-center justify-center w-10 h-10 rounded-lg 
                        bg-indigo-100 text-indigo-600 shadow-inner"
              >
                <MessageSquare size={18} />
              </div>

              <div className="flex flex-col">
                <p className="text-sm font-semibold text-gray-900">{room.title}</p>
                <p className="text-xs text-gray-500 mt-[2px]">{room.userName}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500">
              <div className="flex items-center gap-1.5">
                <Clock size={14} className="text-gray-400" />
                <span>{timeAgo(new Date(room.createdAt))}</span>
              </div>

              <span
                className={clsx(
                  'px-2.5 py-1 rounded-md text-[11px] font-medium border whitespace-nowrap',
                  room.userType === '제조 유통사'
                    ? 'bg-[#F6EDF7] text-[#96257A] border-[#E1B8D9]'
                    : room.userType === '개인 안경원'
                      ? 'bg-[#E9F9F7] text-[#009688] border-[#A9E2D8]'
                      : room.userType === '체인 안경원'
                        ? 'bg-[#ECF2FF] text-[#135D9C] border-[#B6C8F0]'
                        : 'bg-gray-100 text-gray-700 border-gray-300'
                )}
              >
                {room.userType}
              </span>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-auto">
        <Pagination
          pageNum={currentPage}
          totalPages={totalPages}
          onPageChange={(p: number) => {
            if (p < 1 || p > totalPages) return;
            setCurrentPage(p);
          }}
        />
      </div>
    </div>
  );
}
