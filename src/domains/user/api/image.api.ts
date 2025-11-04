import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { GenerateImageResponse, GenerateImageRequest } from '@/domains/user/types/image.type';

// 이미지 생성 요청
export const generateImages = async (payload: GenerateImageRequest) => {
  const { data } = await fastApi.post<ApiEnvelope<{ data: GenerateImageResponse }>>(
    '/api/v1/images/generate',
    payload
  );

  const images = data.result?.data?.images ?? [];
  return images.map(i => ({ image_id: i.image_id, url: i.url }));
};

// 이미지 재생성 요청
export const regenerateImages = async (payload: GenerateImageRequest) => {
  const { data } = await fastApi.post<ApiEnvelope<{ data: GenerateImageResponse }>>(
    '/api/v1/images/regenerate',
    payload
  );

  const images = data.result?.data?.images ?? [];
  return images.map(i => ({ image_id: i.image_id, url: i.url }));
};
