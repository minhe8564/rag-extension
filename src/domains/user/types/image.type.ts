export type GeneratedImage = {
  image_id: string;
  type: string;
  url: string;
};

export type GenerateImageResponse = {
  created_at: string;
  images: GeneratedImage[];
  status: string;
};

export type GenerateImageRequest = {
  image_id?: string;
  prompt: string;
  size?: string;
  style?: string;
};

export type StylePreset =
  | 'poster'
  | 'watercolor'
  | 'flat-illustration'
  | 'anime'
  | 'photoreal'
  | 'pixelart';

export const STYLE_LABEL: Record<StylePreset, string> = {
  poster: '포스터',
  watercolor: '수채화',
  'flat-illustration': '플랫 일러스트',
  anime: '애니',
  photoreal: '사진 실사',
  pixelart: '픽셀아트',
};
