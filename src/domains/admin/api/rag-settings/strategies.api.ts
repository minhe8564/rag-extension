import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  StrategyListResult,
  Strategy,
  GetStrategiesParams,
} from '@/domains/admin/types/rag-settings/strategies.types';

// 전략 목록 조회
export async function getStrategies(params?: GetStrategiesParams) {
  const res = await fastApi.get<ApiEnvelope<StrategyListResult>>('/api/v1/rag/strategies', {
    params,
  });

  return res.data.result.data;
}

// 전략 단건 조회
export async function getStrategyById(strategyNo: string) {
  const res = await fastApi.get<ApiEnvelope<Strategy>>(`/api/v1/rag/strategies/${strategyNo}`);

  return res.data.result;
}

// 전략 생성
export async function createStrategy(payload: Omit<Strategy, 'strategyNo'>) {
  const res = await fastApi.post<ApiEnvelope<Strategy>>('/api/v1/rag/strategies', payload);

  return res.data.result;
}

// 전략 수정
export async function updateStrategy(strategyNo: string, payload: Partial<Strategy>) {
  const res = await fastApi.put<ApiEnvelope<Strategy>>(
    `/api/v1/rag/strategies/${strategyNo}`,
    payload
  );

  return res.data.result;
}

// 전략 삭제
export async function deleteStrategy(strategyNo: string) {
  const res = await fastApi.delete<ApiEnvelope<null>>(`/api/v1/rag/strategies/${strategyNo}`);

  return res.data.result;
}
