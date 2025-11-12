import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { Toggle } from '@/domains/admin/components/rag-settings/ui/Toggle';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';
import PromptManager from '@/domains/admin/components/rag-settings/query/prompt/PromptManager';
import SectionHeader from '@/domains/admin/components/rag-settings/ui/SectionHeader';
import Select from '@/shared/components/Select';
import type { QuerySettingsFieldsProps } from '@/domains/admin/types/rag-settings/query/querySettings.types';

export default function QuerySettingsFields({
  anchors,
  loading,
  scrollTo,

  queryEngine,
  searchAlgorithm,
  topK,
  threshold,
  reranking,
  llmModel,
  temperature,
  multimodal,

  setQueryEngine,
  setSearchAlgorithm,
  setTopK,
  setThreshold,
  setReranking,
  setLlmModel,
  setTemperature,
  setMultimodal,

  transformOpts,
  searchAlgoOpts,
  rerankOpts,
  llmOpts,
}: QuerySettingsFieldsProps) {
  return (
    <>
      <div ref={anchors?.['query-embed']} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="query-embed"
          title="Query Embed · 질의 벡터화"
          subtitle="질의를 변환/확장해 검색 품질을 높입니다."
          icon={PipelineIcons.QueryEmbed}
          onClick={scrollTo}
        />
        <div className="mb-2 flex items-center justify-between gap-4">
          <LabelRow label="질의 변환" hint="HyDE / Buffer 등 변환 전략을 선택하세요." />
          <div className="max-w-xs w-full">
            <Select
              value={queryEngine}
              onChange={setQueryEngine}
              options={transformOpts}
              disabled={loading || transformOpts.length === 0}
            />
          </div>
        </div>
      </div>

      <div ref={anchors?.searching} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="searching"
          title="Searching · 검색"
          subtitle="관련 텍스트 청크를 검색할 알고리즘과 파라미터를 설정합니다."
          icon={PipelineIcons.Searching}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="검색 알고리즘" hint="Semantic 또는 Hybrid 검색 전략을 고르세요." />
          <div className="max-w-xs w-full">
            <Select
              value={searchAlgorithm}
              onChange={setSearchAlgorithm}
              options={searchAlgoOpts}
              disabled={loading || searchAlgoOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="Top-K" hint="쿼리와 가장 유사한 K개의 후보를 검색합니다." />
          <div className="max-w-xs w-full">
            <input
              type="number"
              value={topK}
              onChange={(e) => setTopK(Math.max(1, Number(e.target.value) || 1))}
              min={1}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent text-right"
              disabled={loading}
            />
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow label="유사도 임계값" hint="결과 필터링을 위한 임계값을 설정합니다." />
          <div className="max-w-sm w-full">
            <Slider value={threshold} min={0} max={1} step={0.1} onChange={setThreshold} />
          </div>
        </div>
      </div>

      <div ref={anchors?.reranker} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="reranker"
          title="Re-ranker · 재정렬"
          subtitle="검색된 결과를 의미 기반으로 재정렬하여 정확도를 높입니다."
          icon={PipelineIcons.Reranker}
          onClick={scrollTo}
        />
        <div className="flex items-center justify-between gap-4">
          <LabelRow label="Re-ranking" hint="리랭킹 전략을 선택합니다." />
          <div className="max-w-sm w-full">
            <Select
              value={reranking}
              onChange={setReranking}
              options={rerankOpts}
              disabled={loading || rerankOpts.length === 0}
            />
          </div>
        </div>
      </div>

      <div ref={anchors?.prompting} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="prompting"
          title="Prompting · 프롬프트"
          subtitle="시스템/사용자 프롬프트를 관리합니다."
          icon={PipelineIcons.Prompting}
          onClick={scrollTo}
        />
        <div className="mb-2 flex items-center justify-between gap-4">
          <LabelRow label="시스템 프롬프트 관리" hint="모델의 전체 톤·역할을 지정합니다." />
        </div>
        <PromptManager storageKey="system" />
        <div className="my-2 mt-10 flex items-center justify-between gap-4">
          <LabelRow label="사용자 프롬프트 관리" hint="사용자의 전체 톤·역할을 지정합니다." />
        </div>
        <PromptManager storageKey="user" />
      </div>

      <div ref={anchors?.generation} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="generation"
          title="Generation · 응답 생성"
          subtitle="응답을 생성할 LLM과 파라미터를 설정합니다."
          icon={PipelineIcons.Generation}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="LLM 모델 선택" hint="응답을 생성할 언어 모델을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select
              value={llmModel}
              onChange={setLlmModel}
              options={llmOpts}
              disabled={loading || llmOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="Temperature" hint="모델의 응답 다양성·창의성 정도입니다." />
          <div className="max-w-xs w-full">
            <Slider value={temperature} min={0} max={1} step={0.1} onChange={setTemperature} />
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="멀티모달 활성화"
            hint="이미지·차트 등 비텍스트 입력을 이해해야 할 때만 활성화하세요."
          />
          <div className="flex-shrink-0">
            <Toggle checked={multimodal} onChange={setMultimodal} />
          </div>
        </div>
      </div>
    </>
  );
}
