import { useEffect, useRef } from 'react';

export function AlertModal({
  isOpen,
  onClose,
  notifications,
  onRead,
  onDelete,
}: {
  isOpen: boolean;
  onClose: () => void;
  notifications: {
    notificationNo: string;
    category: string;
    eventType: string;
    referenceId: string;
    title: string;
    total: number;
    successCount: number;
    failedCount: number;
    isRead: boolean;
    createdAt: string;
  }[];
  onRead: (no: string) => void;
  onDelete: (no: string) => void;
}) {
  const modalRef = useRef<HTMLDivElement>(null);

  // 외부 클릭 시 닫힘 처리
  useEffect(() => {
    if (!isOpen) return;

    const handleClick = (e: MouseEvent) => {
      const target = e.target as Node;
      if (modalRef.current?.contains(target)) return;
      onClose();
    };

    document.addEventListener('pointerdown', handleClick);
    return () => document.removeEventListener('pointerdown', handleClick);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={modalRef}
      className="
    absolute right-0 mt-2 w-72 z-[999]
    bg-white rounded-xl shadow-lg border border-gray-200
    max-h-80 overflow-y-auto
  "
    >
      {notifications.length === 0 && (
        <div className="p-4 text-center text-sm text-gray-500">알림이 없습니다.</div>
      )}

      {notifications.map((item) => (
        <div
          key={item.notificationNo}
          className="flex justify-between items-start p-3 border-b last:border-b-0"
        >
          <div className="flex-1 pr-2 flex items-start gap-2 min-w-0">
            {/* 초록불 */}
            <span className="w-2 h-2 rounded-full bg-green-500 mt-1 shrink-0" />

            {/* 텍스트 컬럼 (세로 정렬) */}
            <div className="flex flex-col min-w-0">
              {/* 제목 */}
              <p className="text-sm font-semibold break-keep">{item.title}</p>

              {/* 메시지 */}
              <p className="text-xs text-gray-600 mt-1 break-keep">
                전체 {item.total}개 중 {item.successCount}개 성공 / {item.failedCount}개 실패
              </p>

              {/* 시간 */}
              <p className="text-[10px] text-gray-400 mt-1">
                {new Date(item.createdAt).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-1 ml-2 shrink-0">
            {!item.isRead && (
              <button
                onClick={() => onRead(item.notificationNo)}
                className="
        text-[10px] px-2 py-[3px]
        rounded-md
        bg-blue-50 text-blue-600
        hover:bg-blue-100 hover:text-blue-700
        transition-colors
      "
              >
                읽음
              </button>
            )}

            <button
              onClick={() => onDelete(item.notificationNo)}
              className="
      text-[10px] px-2 py-[3px]
      rounded-md
      bg-red-50 text-red-600
      hover:bg-red-100 hover:text-red-700
      transition-colors
    "
            >
              삭제
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
