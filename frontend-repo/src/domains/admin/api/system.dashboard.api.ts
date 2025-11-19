import springApi from '@/shared/lib/apiInstance';
import type {
  ServicesPerformanceResponse,
  ServicesStatusResponse,
  StorageUsageResponse,
  RagPipelineResponseTimeResponse,
} from '@/domains/admin/types/system.dashboard.types';

// 9개 서비스 성능
export async function getServicesPerformance() {
  const res = await springApi.get<ServicesPerformanceResponse>(`/api/v1/monitoring/services`);
  return res.data.result;
}

// 9개 서비스 실행 상태
export async function getServicesStatus() {
  const res = await springApi.get<ServicesStatusResponse>(`/api/v1/monitoring/services/status`);
  return res.data.result;
}

// 파일시스템 사용량
export async function getStorageUsage() {
  const res = await springApi.get<StorageUsageResponse>(`/api/v1/monitoring/storage`);
  return res.data.result;
}

// RAG Pipeline 평균 응답시간 조회
export async function getRagPipelineResponseTime() {
  const res = await springApi.get<RagPipelineResponseTimeResponse>(
    `/api/v1/monitoring/metrics/rag`
  );
  return res.data.result;
}
