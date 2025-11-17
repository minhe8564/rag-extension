import { create } from 'zustand';
import type { IngestSummaryResponse } from '@/shared/types/ingest.types';

export type NotificationType = 'INGEST_SUMMARY';

export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
  payload?: IngestSummaryResponse;
}

interface NotificationState {
  notifications: NotificationItem[];
  hasUnread: boolean;
  addIngestNotification: (data: IngestSummaryResponse) => void;
  markAllRead: () => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set, _get) => ({
  notifications: [],
  hasUnread: false,

  addIngestNotification: (data) => {
    const { result } = data;
    const now = new Date().toISOString();

    const title = '문서 인입이 완료되었습니다.';
    const message = `전체 ${result.total}개 중 ${result.successCount}개 성공, ${result.failedCount}개 실패`;

    const item: NotificationItem = {
      id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'INGEST_SUMMARY',
      title,
      message,
      createdAt: now,
      read: false,
      payload: data,
    };

    set((state) => ({
      notifications: [item, ...state.notifications],
      hasUnread: true,
    }));
  },

  markAllRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      hasUnread: false,
    }));
  },

  clearAll: () => {
    set(() => ({
      notifications: [],
      hasUnread: false,
    }));
  },
}));
