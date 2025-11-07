import { useEffect, useMemo, useState } from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import Card from '@/shared/components/Card';
import Pagination from '@/shared/components/Pagination';
import { getChatRooms } from '@/domains/admin/api/dashboard.api';
import type { createdChatrooms, chatroomTimeframe } from '@/domains/admin/types/dashboard.types';

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
      console.log('✅ 생성된 채팅방 데이터:', result);
      setChatrooms(result.chatrooms);
      setTimeframe(result.timeframe);
    };
    fetchData();
  }, []);

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;
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
    <Card title="생성된 채팅방" subtitle="최근 활동 기준" className="p-4">
      <ul className="flex flex-col gap-2">
        {pageItems.map((room, i) => (
          <li
            key={`${room.chatRoomId}-${startIndex + i}`}
            className="flex items-center justify-between p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition"
          >
            {/* 왼쪽: 아이콘 + 정보 */}
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-md bg-indigo-100 text-indigo-600">
                <MessageSquare size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-800">{room.chatTitle}</p>
                <p className="text-xs text-gray-500">{room.userName}</p>
              </div>
            </div>

            {/* 오른쪽: 메시지 수, 시간, 상태 */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <Clock size={14} />
                <span>{timeAgo(new Date(room.createdAt))}</span>
              </div>

              <span
                className={`px-2 py-0.5 rounded-md text-xs font-medium border
                ${
                  room.userType === '제조 유통사'
                    ? 'bg-[#F6EDF7] text-[#96257A] border-[#E1B8D9]' // 보라 (HEEBEES)
                    : room.userType === '개인 안경원'
                      ? 'bg-[#E9F9F7] text-[#009688] border-[#A9E2D8]' // 민트 (상업/체인)
                      : room.userType === '체인 안경원'
                        ? 'bg-[#ECF2FF] text-[#135D9C] border-[#B6C8F0]' // 블루 (Retina)
                        : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}
              >
                {room.userType}
              </span>
            </div>
          </li>
        ))}
      </ul>
      <Pagination
        pageNum={currentPage}
        totalPages={totalPages}
        onPageChange={(p: number) => {
          if (p < 1 || p > totalPages) return;
          setCurrentPage(p);
        }}
      />
    </Card>
  );
}
