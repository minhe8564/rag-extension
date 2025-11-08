import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  ChangeTrend,
  TotalCount,
  chatbotUsageTime,
  modelTokenTime,
  chatbotUsageHeatmap,
  frequentKeywords,
  errorList,
  createdChatrooms,
} from '@/domains/admin/types/rag.dashboard.types';

// 사용자 수 조회
export const getUserCount = async () => {
  await springApi.get<{ event: string; data: { accessUsers: number } }>(
    '/api/v1/analytics/metrics/access-users/stream'
  );
};

// 총 사용자 수 조회
export const getTotalUserCount = async () => {
  const { data } = await springApi.get<ApiEnvelope<TotalCount>>(
    '/api/v1/analytics/metrics/access-users/total'
  );
  return data.result;
};

// 24시간 사용자 증감률 조회
export const getUserChangeTrend = async () => {
  const { data } = await springApi.get<ApiEnvelope<ChangeTrend>>(
    '/api/v1/analytics/metrics/access-users/change-24h'
  );
  return data.result;
};

// 업로드 문서 수 조회
export const getDocumentCount = async () => {
  await springApi.get<{ event: string; data: { uploadedDocs: number } }>(
    '/api/v1/analytics/metrics/upload-documents/stream'
  );
};

// 총 업로드 문서 수 조회
export const getTotalDocumentCount = async () => {
  const { data } = await springApi.get<ApiEnvelope<TotalCount>>(
    '/api/v1/analytics/metrics/upload-documents/total'
  );
  return data.result;
};

// 24시간 업로드 문서 증감률 조회
export const getDocumentChangeTrend = async () => {
  const { data } = await springApi.get<ApiEnvelope<ChangeTrend>>(
    '/api/v1/analytics/metrics/upload-documents/change-24h'
  );
  return data.result;
};

// 오류 발생 수 조회
export const getErrorCount = async () => {
  await springApi.get<{ event: string; data: { errorCount: number } }>(
    '/api/v1/analytics/metrics/errors/stream'
  );
};

// 총 발생한 오류 수 조회
export const getTotalErrorCount = async () => {
  const { data } = await springApi.get<ApiEnvelope<TotalCount>>(
    '/api/v1/analytics/metrics/errors/total'
  );
  return data.result;
};

// 24시간 오류 발생 증감률 조회
export const getErrorChangeTrend = async () => {
  const { data } = await springApi.get<ApiEnvelope<ChangeTrend>>(
    '/api/v1/analytics/metrics/errors/change-24h'
  );
  return data.result;
};

// 챗봇 사용량 시계열 조회
export const getChatbotUsageTimeSeries = async (params: { granularity: string }) => {
  const { data } = await springApi.get<ApiEnvelope<chatbotUsageTime>>(
    '/api/v1/analytics/metrics/chatbot/timeseries',
    { params }
  );
  return data.result;
};

// 모델별 토큰 사용량 + 응답시간 시계열 조회
export const getModelTokenUsageTimeSeries = async (params: { granularity: string }) => {
  const { data } = await springApi.get<ApiEnvelope<modelTokenTime>>(
    '/api/v1/analytics/metrics/models/timeseries',
    { params }
  );
  return data.result;
};

// 시간대별 챗봇 사용량 히트맵 조회
export const getChatbotUsageHeatmap = async () => {
  const { data } = await springApi.get<ApiEnvelope<chatbotUsageHeatmap>>(
    '/api/v1/analytics/metrics/chatbot/heatmap'
  );
  return data.result;
};

// 자주 물어보는 키워드 조회
export const getKeywords = async () => {
  const { data } = await springApi.get<ApiEnvelope<frequentKeywords>>(
    '/api/v1/analytics/trends/keywords'
  );
  return data.result;
};

// 발생한 오류 목록 조회
export const getErrorLogs = async () => {
  const { data } = await springApi.get<ApiEnvelope<errorList>>('/api/v1/analytics/errors/today');
  return data.result;
};

// 생성된 채팅방 목록 조회
export const getChatRooms = async () => {
  const { data } = await springApi.get<ApiEnvelope<createdChatrooms>>(
    '/api/v1/analytics/chatrooms/today'
  );
  return data.result;
};
