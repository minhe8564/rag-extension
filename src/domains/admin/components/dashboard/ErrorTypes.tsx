import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, GaugeCircle, Cpu } from 'lucide-react';
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
  errors: [
    {
      chatTitle: '상품 검색 챗봇',
      userType: '일반 사용자',
      userName: '홍길동',
      chatRoomId: 'room-001',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 2 * 60 * 1000), // 2분 전
    },
    {
      chatTitle: '데이터 분석 챗봇',
      userType: '관리자',
      userName: '최유진',
      chatRoomId: 'room-002',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 7 * 60 * 1000), // 7분 전
    },
    {
      chatTitle: '고객센터 문의',
      userType: '관리자',
      userName: '김지원',
      chatRoomId: 'room-003',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 20 * 60 * 1000), // 20분 전
    },
    {
      chatTitle: '문서 검색 챗봇',
      userType: '일반 사용자',
      userName: '이현우',
      chatRoomId: 'room-004',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 45 * 60 * 1000), // 45분 전
    },
    {
      chatTitle: 'AI 응답 요약 서비스',
      userType: '관리자',
      userName: '박지민',
      chatRoomId: 'room-005',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 1.5 * 60 * 60 * 1000), // 1시간 30분 전
    },
    {
      chatTitle: '챗봇 관리 대시보드',
      userType: '관리자',
      userName: '강서현',
      chatRoomId: 'room-006',
      errorType: 'SYSTEM',
      occurredAt: new Date(Date.now() - 3 * 60 * 60 * 1000), // 3시간 전
    },
    {
      chatTitle: '고객 응대 자동화',
      userType: '일반 사용자',
      userName: '정우성',
      chatRoomId: 'room-007',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 50 * 60 * 1000), // 50분 전
    },
    {
      chatTitle: '예약 확인 챗봇',
      userType: '관리자',
      userName: '김수진',
      chatRoomId: 'room-008',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 2.5 * 60 * 60 * 1000), // 2시간 30분 전
    },
    {
      chatTitle: 'AI 상품 추천 서비스',
      userType: '일반 사용자',
      userName: '이민재',
      chatRoomId: 'room-009',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4시간 전
    },
    {
      chatTitle: '고객 피드백 챗봇',
      userType: '일반 사용자',
      userName: '한지민',
      chatRoomId: 'room-010',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5시간 전
    },
    {
      chatTitle: 'CS 자동 분류 시스템',
      userType: '관리자',
      userName: '정해인',
      chatRoomId: 'room-011',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 8 * 60 * 60 * 1000), // 8시간 전
    },
    {
      chatTitle: '음성 인식 챗봇',
      userType: '일반 사용자',
      userName: '박서준',
      chatRoomId: 'room-012',
      errorType: '응답오류',
      occurredAt: new Date(Date.now() - 10 * 60 * 60 * 1000), // 10시간 전
    },
  ],
};

export default function ErrorTypes() {
  const [errors, _setErrors] = useState(dummyResponse.errors);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;
  const sortedErrors = useMemo(
    () =>
      [...errors].sort(
        (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime()
      ),
    [errors]
  );
  const totalPages = Math.max(1, Math.ceil(sortedErrors.length / pageSize));

  useEffect(() => {
    // 실제 API 연동 시 이 부분에서 setErrors() 호출
  }, []);

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

  const startIndex = (currentPage - 1) * pageSize;
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
