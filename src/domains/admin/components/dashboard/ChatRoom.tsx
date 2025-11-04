import { useMemo, useState } from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import Card from '@/shared/components/Card';
import Pagination from '@/shared/components/Pagenation';

// 시간 경과 계산 함수
function timeAgo(date: Date) {
  const diff = Math.floor((Date.now() - date.getTime()) / 60000); // 분 단위
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  const hours = Math.floor(diff / 60);
  return `${hours}시간 전`;
}

// 더미
const dummyResponse = {
  timeframe: {
    start: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString(),
  },
  chatrooms: [
    {
      chatTitle: '렌즈 주문 오류 문의',
      userType: '개인 안경점',
      userName: '시선안경 강민수 원장',
      chatRoomId: 'room_7f3a2b',
      createdAt: new Date(Date.now() - 8 * 60 * 1000).toISOString(), // 8분 전
    },
    {
      chatTitle: '납품 일정 조정 요청',
      userType: '체인 안경점',
      userName: '스마트안경 명동점',
      chatRoomId: 'room_b5d9e1',
      createdAt: new Date(Date.now() - 25 * 60 * 1000).toISOString(), // 25분 전
    },
    {
      chatTitle: '신제품 렌즈 스펙 문의',
      userType: '제조사',
      userName: '클리어옵틱스 기술팀',
      chatRoomId: 'room_c9a8t2',
      createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45분 전
    },
    {
      chatTitle: '주문서 수정 요청',
      userType: '개인 안경점',
      userName: '안경명가 부평점',
      chatRoomId: 'room_d2e1k5',
      createdAt: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(), // 1시간 30분 전
    },
    {
      chatTitle: '렌즈 단가 협의',
      userType: '제조사',
      userName: '루멘코 산업영업팀',
      chatRoomId: 'room_e3p9x4',
      createdAt: new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString(), // 2시간 30분 전
    },
    {
      chatTitle: '재고 수량 확인',
      userType: '체인 안경점',
      userName: '글라스핏 강남본점',
      chatRoomId: 'room_f7g1r3',
      createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4시간 전
    },
    {
      chatTitle: '렌즈 불량 교환 문의',
      userType: '개인 안경점',
      userName: '밝은시안경 수원점',
      chatRoomId: 'room_h2q5t7',
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5시간 전
    },
    {
      chatTitle: '출고 지연 관련 문의',
      userType: '제조사',
      userName: '아이리드 제조관리팀',
      chatRoomId: 'room_m9z8k2',
      createdAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(), // 8시간 전
    },
    {
      chatTitle: '매장 프로모션 이미지 요청',
      userType: '체인 안경점',
      userName: '스펙트라 신촌점',
      chatRoomId: 'room_n3b7v4',
      createdAt: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(), // 10시간 전
    },
    {
      chatTitle: '시력측정기 연결 오류',
      userType: '개인 안경점',
      userName: '굿아이안경 이정훈 원장',
      chatRoomId: 'room_x1a5l8',
      createdAt: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(), // 18시간 전
    },
  ],
};

export default function ChatRoom() {
  const { chatrooms } = dummyResponse;
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;
  const sortedRooms = useMemo(
    () =>
      [...chatrooms].sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      ),
    []
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
                  room.userType === '개인 안경점'
                    ? 'bg-[#F6EDF7] text-[#96257A] border-[#E1B8D9]' // 보라 (HEEBEES)
                    : room.userType === '체인 안경점'
                      ? 'bg-[#E9F9F7] text-[#009688] border-[#A9E2D8]' // 민트 (상업/체인)
                      : room.userType === '제조사'
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
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={(p) => {
          if (p < 1 || p > totalPages) return;
          setCurrentPage(p);
        }}
      />
    </Card>
  );
}
