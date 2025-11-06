import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  GeneratedImage,
  GenerateImageResponse,
  GenerateImageRequest,
} from '@/domains/user/types/image.type';

// 이미지 생성 요청
export const generateImages = async (payload: GenerateImageRequest) => {
  const { data } = await fastApi.post<ApiEnvelope<{ data: GenerateImageResponse }>>(
    '/api/v1/images/generate',
    payload
  );

  const images = data.result?.data?.images ?? [];
  return images.map((i) => ({ image_id: i.image_id, url: i.url }));
};

// 이미지 재생성 요청
export const regenerateImages = async (payload: GenerateImageRequest) => {
  const { data } = await fastApi.post<ApiEnvelope<{ data: GenerateImageResponse }>>(
    '/api/v1/images/regenerate',
    payload
  );

  const images = data.result?.data?.images ?? [];
  return images.map((i) => ({ image_id: i.image_id, url: i.url }));
};

// 내가 생성한 이미지 목록 조회
export const getUserImages = async (): Promise<GeneratedImage[]> => {
  const { data } = await fastApi.get<ApiEnvelope<{ data: GeneratedImage[] }>>('/api/v1/images');
  return data.result?.data ?? [];
};

// 이미지 상세 조회
export const getImageDetail = async (imageId: string): Promise<GenerateImageResponse> => {
  const { data } = await fastApi.get<ApiEnvelope<GenerateImageResponse>>(
    `/api/v1/images/${imageId}`
  );
  return data.result;
};

// 이미지 삭제
export const deleteImage = async (imageId: string): Promise<boolean> => {
  const res = await fastApi.delete(`/api/v1/images/${imageId}`);
  return res.status === 204;
};
