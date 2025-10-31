import { useState } from 'react';
import Card from '@/shared/components/Card';
import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import Select from '@/shared/components/Select';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { Toggle } from '@/domains/admin/components/rag-settings/ui/Toggle';
import { Save } from 'lucide-react';
import {
  queryTransFormOptions,
  searchAlgorithmOptions,
  queryTemplateOptions,
  rerankingOptions,
  llmModelsOptions,
} from '@/domains/admin/components/rag-settings/options';

type SavePayload = {
  template: string;
  queryEngine: string;
  searchAlgorithm: string;
  topK: number;
  threshold: number;
  reranking: string;
  llmModel: string;
  temperature: number;
  multimodal: boolean;
};

export function QuerySettingsForm({
  template,
  onTemplateChange,
  onSave,
}: {
  template: string;
  onTemplateChange: (v: string) => void;
  onSave?: (payload: SavePayload) => void | Promise<void>;
}) {
  // 벡터 인덱싱 및 검색 설정
  const [queryEngine, setQueryEngine] = useState('hyde');
  const [searchAlgorithm, setSearchAlgorithm] = useState('semantic');
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.2);
  const [reranking, setReranking] = useState('pointwise');

  // LLM 설정
  const [llmModel, setLlmModel] = useState('gpt-4o');
  const [temperature, setTemperature] = useState(0.2);
  const [multimodal, setMultimodal] = useState(false);

  const handleSave = async () => {
    const payload: SavePayload = {
      template,
      queryEngine,
      searchAlgorithm,
      topK,
      threshold,
      reranking,
      llmModel,
      temperature,
      multimodal,
    };

    try {
      await onSave?.(payload);
      alert('설정이 저장되었습니다.');
    } catch (e) {
      console.error(e);
      alert('설정 저장 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="Query 파이프라인 템플릿"
        tip="자주 사용하는 설정을 템플릿으로 저장해 빠르게 불러올 수 있어요."
      >
        <div className="flex items-center gap-4">
          <div className="max-w-xs w-full">
            <Select
              value={template}
              onChange={onTemplateChange}
              options={queryTemplateOptions as any}
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

      <Card title="벡터 인덱싱 및 검색 설정">
        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="질의 변환" hint="질의를 변환해 검색 품질을 향상시킵니다." />
          <div className="max-w-xs w-full">
            <Select
              value={queryEngine}
              onChange={setQueryEngine}
              options={queryTransFormOptions as any}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="검색 알고리즘" hint="관련 텍스트 청크를 검색할 알고리즘을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select
              value={searchAlgorithm}
              onChange={setSearchAlgorithm}
              options={searchAlgorithmOptions as any}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="Top-K" hint="쿼리 벡터와 가장 유사한 K개의 벡터를 검색합니다." />
          <div className="max-w-xs w-full">
            <input
              type="number"
              value={topK}
              onChange={e => setTopK(Math.max(1, Number(e.target.value) || 1))}
              min={1}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-base
                focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent
                text-right"
              placeholder="예: 5"
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="유사도 임계값" hint="결과 필터링을 위한 유사도 임계값을 설정합니다." />
          <div className="max-w-sm w-full">
            <Slider value={threshold} min={0} max={1} step={0.1} onChange={setThreshold} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <LabelRow label="Re-ranking" hint="검색된 결과의 순위를 재조정하여 정확도를 높입니다." />
          <div className="max-w-sm w-full">
            <Select value={reranking} onChange={setReranking} options={rerankingOptions as any} />
          </div>
        </div>
      </Card>

      <Card title="시스템 프롬프트 설정">
        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="시스템 프롬프트 관리" hint="모델의 전체 톤이나 역할을 지정합니다." />
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow label="사용자 프롬프트 관리" hint="사용자의 전체 톤이나 역할을 지정합니다." />
        </div>
      </Card>

      <Card title="LLM 설정">
        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="LLM 모델 선택" hint="응답을 생성할 언어 모델을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select value={llmModel} onChange={setLlmModel} options={llmModelsOptions as any} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <LabelRow label="Temperature" hint="모델의 응답 다양성과 창의성을 조절합니다." />
          <div className="max-w-xs w-full">
            <Slider value={temperature} min={0} max={1} step={0.1} onChange={setTemperature} />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="멀티 모달 활성화"
            hint="이미지·차트 등 비텍스트 입력을 이해해야 할 때만 활성화합니다."
          />
          <div className="flex-shrink-0">
            <Toggle
              checked={multimodal}
              onChange={v => {
                setMultimodal(v);
                console.log('toggle multimodal', v);
              }}
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
