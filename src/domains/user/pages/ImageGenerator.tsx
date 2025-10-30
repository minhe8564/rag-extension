import { useState } from 'react';
import apiInstance from '@/shared/lib/apiInstance';
import { toast } from 'react-toastify';
import type { GenSize, StylePreset } from '@/domains/user/types/image.type';
import ImageGeneratorForm from '@/domains/user/components/ImageGeneratorForm';
import ImageResultPane from '@/domains/user/components/ImageResultPane';

type GenerateReq = { prompt: string; size: GenSize; style?: StylePreset };
type GenerateRes = { images: string[] };

export default function ImageGenerator() {
  // 좌측 폼 상태
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState<GenSize>('768x768');
  const [style, setStyle] = useState<StylePreset>('poster');

  // 우측 결과 상태
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const MAX_LEN = 300;
  const disabled = loading || !prompt.trim();

  const onGenerate = async (_override?: Partial<GenerateReq>) => {
    if (!prompt.trim()) return;
    setLoading(true);

    const body: GenerateReq = { prompt, size, style, ..._override };
    try {
      const { data } = await apiInstance.post<GenerateRes>('/api/images/generate', body);
      if (!data?.images?.length) {
        toast.error('이미지를 생성하지 못했어요. 프롬프트를 조금 더 구체화해 보세요.');
        return;
      }
      setImages(data.images);
    } catch {
      toast.error('이미지 생성 중 오류가 발생했어요.');
    } finally {
      setLoading(false);
    }
  };

  const onDownload = async (src: string, idx: number) => {
    try {
      const res = await fetch(src);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `retina-image-${idx + 1}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(a.href);
    } catch {
      toast.error('다운로드에 실패했어요.');
    }
  };

  const onCopy = async (src: string) => {
    try {
      const res = await fetch(src);
      let blob = await res.blob();

      // webp는 환경에 따라 ClipboardItem 실패 → 주소 복사로 폴백
      // @ts-ignore
      if (typeof ClipboardItem !== 'undefined' && blob.type !== 'image/webp') {
        // @ts-ignore
        await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
        toast.success('이미지를 클립보드로 복사했어요.');
      } else {
        await navigator.clipboard.writeText(src);
        toast.info('이미지 주소를 복사했어요.');
      }
    } catch {
      toast.error('복사에 실패했어요.');
    }
  };

  const onReusePrompt = (addition?: string) => {
    const next = (prompt.trim() + (addition ? ` ${addition}` : '')).slice(0, MAX_LEN);
    setPrompt(next);
    toast.info('프롬프트에 적용했어요.');
  };

  return (
    <section className="h-full grid grid-cols-1 lg:grid-cols-[600px_1fr] gap-6">
      <ImageGeneratorForm
        prompt={prompt}
        setPrompt={setPrompt}
        size={size}
        setSize={setSize}
        style={style}
        setStyle={setStyle}
        loading={loading}
        disabled={disabled}
        maxLen={MAX_LEN}
        onGenerate={onGenerate}
        onReusePrompt={onReusePrompt}
      />

      <ImageResultPane
        images={images}
        loading={loading}
        style={style}
        size={size}
        onDownload={onDownload}
        onCopy={onCopy}
        onRegenerate={() => onGenerate()}
      />
    </section>
  );
}
