import { useMemo, useState } from 'react';
import Card from '@/domains/admin/components/rag-settings/ui/Card';
import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Select } from '@/domains/admin/components/rag-settings/ui/Select';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { Save } from 'lucide-react';
import {
  chunkStrategyOptions,
  embedOptions,
  extractOptions,
  ingestTemplateOptions,
} from '@/domains/admin/components/rag-settings/options';
import { toast } from 'react-toastify';

type SavePayload = {
  template: string;
  extractEngine: string;
  chunkStrategy: string;
  chunkSize: number;
  overlap: number;
  embedModel: string;
  embedBackup: string;
};
export function IngestSettingsForm({
  template,
  onTemplateChange,
  onSave,
}: {
  template: string;
  onTemplateChange: (v: string) => void;
  onSave?: (payload: SavePayload) => void | Promise<void>;
}) {
  // 추출 과정
  const [extractEngine, setExtractEngine] = useState('pdfplumber');

  // 데이터 전처리
  const [chunkStrategy, setChunkStrategy] = useState('paragraph');
  const [chunkSize, setChunkSize] = useState(512);
  const [overlap, setOverlap] = useState(40);

  // 임베딩
  const [embedModel, setEmbedModel] = useState('multilingual-e5-large');
  const [embedBackup, setEmbedBackup] = useState('bge');

  const handleSave = async () => {
    const payload: SavePayload = {
      template,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedBackup,
    };

    try {
      await onSave?.(payload);
      toast.success('설정이 저장되었습니다.');
    } catch (e) {
      console.error(e);
      toast.error('설정 저장에 실패했습니다.');
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="Ingest 파이프라인 템플릿"
        tip="자주 사용하는 설정을 템플릿으로 저장해 빠르게 불러올 수 있어요."
      >
        <div className="flex items-center gap-4">
          <div className="max-w-xs w-full">
            <Select
              value={template}
              onChange={onTemplateChange}
              options={ingestTemplateOptions as any}
            />
          </div>

          <button
            type="button"
            onClick={handleSave}
            className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium
               text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Save size={16} strokeWidth={2} />
            저장
          </button>
        </div>
      </Card>

      <Card title="추출 과정">
        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="추출 엔진 선택"
            hint="문서에서 텍스트, 이미지, 표를 추출하는 방법을 선택합니다."
          />
          <div className="max-w-xs w-full">
            <Select
              value={extractEngine}
              onChange={setExtractEngine}
              options={extractOptions as any}
            />
          </div>
        </div>
      </Card>

      <Card title="데이터 전처리">
        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="청킹 전략 선택" hint="문서를 나누는 기준을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select
              value={chunkStrategy}
              onChange={setChunkStrategy}
              options={chunkStrategyOptions as any}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow
            label="청크 크기"
            hint="큰 청크는 더 많은 컨텍스트를 포함하고, 작은 청크는 정확도를 높입니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={chunkSize} min={1} max={512} onChange={setChunkSize} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="오버랩 토큰 수"
            hint="토큰 수가 클수록 컨텍스트 연속성은 좋지만, 중복성은 증가합니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={overlap} min={0} max={200} step={1} onChange={setOverlap} />
          </div>
        </div>
      </Card>

      <Card title="임베딩 설정">
        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow
            label="임베딩 모델"
            hint="텍스트를 벡터로 변환할 기본 임베딩 모델을 지정합니다.
              검색 정확도와 언어 대응력에 영향을 줍니다."
          />
          <div className="max-w-sm w-full">
            <Select value={embedModel} onChange={setEmbedModel} options={embedOptions as any} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="추가 임베딩 모델"
            hint="텍스트를 벡터로 변환할 보조 모델을 함께 설정합니다.
              여러 모델을 병행해 도메인 대응력을 높일 수 있습니다."
          />
          <div className="max-w-sm w-full">
            <Select value={embedBackup} onChange={setEmbedBackup} options={embedOptions as any} />
          </div>
        </div>
      </Card>
    </div>
  );
}
