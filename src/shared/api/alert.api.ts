import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { GetAlertRequest, AlertResponse } from '@/shared/types/alert.types';

export async function fetchNotifications(params: GetAlertRequest) {
  const { data } = await springApi.get<ApiEnvelope<AlertResponse>>('api/v1/notifications', {
    params,
  });

  return data.result;
}

export async function markNotificationAsRead(notificationNo: string) {
  const { data } = await springApi.patch<ApiEnvelope<void>>(
    `api/v1/notifications/${notificationNo}/read`
  );
  return data.result;
}

export async function deleteNotification(notificationNo: string) {
  const { data } = await springApi.delete<ApiEnvelope<void>>(
    `api/v1/notifications/${notificationNo}`
  );
  return data.result;
}
