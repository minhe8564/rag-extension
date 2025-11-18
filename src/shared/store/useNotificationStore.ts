import { create } from 'zustand';
import type { IngestSummaryResponse } from '@/shared/types/ingest.types';

export interface NotificationItem {
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
}

interface NotificationState {
  realtime: NotificationItem[];
  hasUnreadRealtime: boolean;
  addIngestNotification: (data: IngestSummaryResponse) => void;

  clearRealtime: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  realtime: [],
  hasUnreadRealtime: false,

  addIngestNotification: (data) => {
    const now = new Date().toISOString();
    const r = data.result;

    const item: NotificationItem = {
      notificationNo: `SSE-${now}`,
      category: 'INGEST',
      eventType: 'INGEST_SUMMARY_COMPLETED',
      referenceId: '',
      title: '문서 수집이 완료되었습니다.',
      total: r.total,
      successCount: r.successCount,
      failedCount: r.failedCount,
      isRead: false,
      createdAt: now,
    };

    set((state) => ({
      realtime: [item, ...state.realtime],
      hasUnreadRealtime: true,
    }));
  },

  // SSE 실시간 알림 전체 초기화
  clearRealtime: () =>
    set({
      realtime: [],
      hasUnreadRealtime: false,
    }),
}));
