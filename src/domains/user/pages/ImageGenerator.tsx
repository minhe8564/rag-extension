import { Image } from 'lucide-react';
import ImageGeneratorForm from '@/domains/user/components/image/ImageGeneratorForm';
import ImageResultPane from '@/domains/user/components/image/ImageResultPanel';
import { useState } from 'react';
import { toast } from 'react-toastify';
import { generateImages } from '@/domains/user/api/image.api';
import type { GenerateImageRequest, StylePreset } from '@/domains/user/types/image.type';

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
      if (!urls.length)
        return toast.error('이미지를 생성하지 못했어요. 프롬프트를 구체화해 보세요.');
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
      if (!urls.length) return toast.error('이미지를 다시 생성하지 못했어요.');
      setImages(urls);
    } catch (err) {
      console.error('regenerateImages error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (src: string, idx?: number) => {
    try {
      const resp = await fetch(src, { mode: 'cors' });
      const blob = await resp.blob();
      const ext = (blob.type?.split('/')?.[1] || 'png').split('+')[0];
      const filename = `image-${style}-${size}-${(idx ?? 0) + 1}-${Date.now()}.${ext}`.replace(
        /\s+/g,
        '_'
      );

      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch {
      window.open(src, '_blank', 'noopener,noreferrer');
    }
  };

  const handleCopy = async (src: string) => {
    try {
      if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
        const resp = await fetch(src, { mode: 'cors' });
        const blob = await resp.blob();
        const item = new ClipboardItem({ [blob.type]: blob });
        await navigator.clipboard.write([item]);
        toast.success('이미지가 복사되었습니다.');
        return;
      }
      await navigator.clipboard.writeText(src);
      toast.success('이미지 URL을 복사했습니다.');
    } catch {
      // toast.error('복사에 실패했어요.');
    }
  };

  return (
    <div className="space-y-8 px-4 mb-20">
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
          onReusePrompt={(t) => setPrompt((prev) => prev + ' ' + t)}
          brand="retina"
        />

        <ImageResultPane
          images={images}
          loading={loading}
          style={style}
          size={size}
          onDownload={handleDownload}
          onCopy={handleCopy}
          onRegenerate={(id) => onRegenerate(id)}
        />
      </section>
    </div>
  );
}
