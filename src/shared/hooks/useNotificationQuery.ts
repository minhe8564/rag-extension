// useNotificationsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchNotifications,
  markNotificationAsRead,
  deleteNotification,
} from '@/shared/api/alert.api';
import type { GetAlertRequest } from '@/shared/types/alert.types';

export const useNotificationsQuery = (params: GetAlertRequest, enabled: boolean) => {
  return useQuery({
    queryKey: ['notifications', params],
    queryFn: () => fetchNotifications(params),
    enabled: enabled,
    staleTime: 1000 * 30,
  });
};

export const useMarkReadMutation = () => {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => markNotificationAsRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};

export const useDeleteNotificationMutation = () => {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteNotification(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};

// // SSE 훅
// export function useIngestSSE() {
//   const token = useAuthStore((state) => state.accessToken);
//   const SPRING_API_BASE_URL = import.meta.env.VITE_SPRING_BASE_URL;

//   const addIngestNotification = useNotificationStore((s) => s.addIngestNotification);

//   useEffect(() => {
//     const sources = new EventSourcePolyfill(`${SPRING_API_BASE_URL}/ingest/notify/stream`, {
//       headers: {
//         Authorization: `Bearer ${token}`,
//       },
//     });
//     sources.addEventListener('ingest-summary-completed', (event) => {
//       const payload = JSON.parse((event as MessageEvent).data);
//       addIngestNotification(payload);
//     });

//     return () => sources.close();
//   }, [addIngestNotification, token]);
// }
