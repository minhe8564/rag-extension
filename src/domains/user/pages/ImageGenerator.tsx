import { Image } from 'lucide-react';
import ImageGeneratorForm from '@/domains/user/components/ImageGeneratorForm';
import ImageResultPane from '@/domains/user/components/ImageResultPane';
import { useState } from 'react';
import { toast } from 'react-toastify';
import { generateImages } from '@/domains/user/api/image.api';
import type { GenerateImageRequest } from '@/domains/user/types/image.type';
import type { StylePreset } from '@/domains/user/types/image.type';

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState<string>('1024x1024');
  const [style, setStyle] = useState<StylePreset>('poster');
  const [images, setImages] = useState<{ image_id: string; url: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const MAX_LEN = 300;
  const disabled = loading || !prompt.trim();

  const onGenerate = async (_override?: Partial<GenerateImageRequest>) => {
    if (!prompt.trim()) return;
    setLoading(true);
    const body: GenerateImageRequest = { prompt, size, style, ..._override };

    try {
      const urls = await generateImages(body);
      if (!urls.length) {
        toast.error('이미지를 생성하지 못했어요. 프롬프트를 구체화해 보세요.');
        return;
      }
      setImages(urls);
    } catch (err) {
      console.error('generateImages error:', err);
    } finally {
      setLoading(false);
    }
  };

  const onRegenerate = async (image_id: string) => {
    if (!prompt.trim()) return;
    setLoading(true);
    const body: GenerateImageRequest & { image_id: string } = { image_id, prompt, size, style };

    try {
      const urls = await generateImages(body);
      if (!urls.length) {
        toast.error('이미지를 다시 생성하지 못했어요.');
        return;
      }
      setImages(urls);
    } catch (err) {
      console.error('regenerateImages error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 px-4 mb-20">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-[var(--color-retina-bg)] flex items-center justify-center">
          <Image size={26} className="text-[var(--color-retina)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold mb-1">이미지 생성</h1>
          <p className="text-sm text-gray-600">
            프롬프트를 입력하고 옵션을 선택해 AI로 이미지를 생성하세요.
          </p>
        </div>
      </div>

      {/* 본문 */}
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
          onReusePrompt={t => setPrompt(prev => prev + ' ' + t)}
        />

        <ImageResultPane
          images={images}
          loading={loading}
          style={style}
          size={size}
          onDownload={(src, idx) => console.log('download', src, idx)}
          onCopy={src => console.log('copy', src)}
          onRegenerate={id => onRegenerate(id)}
        />
      </section>
    </div>
  );
}
