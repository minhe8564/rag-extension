import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';
import PromptManager from '@/domains/admin/components/rag-settings/query/prompt/PromptManager';
import SectionHeader from '@/domains/admin/components/rag-settings/ui/SectionHeader';
import Select from '@/shared/components/controls/Select';
import type { QuerySettingsFieldsProps } from '@/domains/admin/types/rag-settings/query/querySettings.types';

export default function QuerySettingsFields({
  anchors,
  loading,
  scrollTo,

  transformation,
  searchAlgorithm,
  reranking,
  llmModel,
  temperature,

  setTransformation,
  setSearchAlgorithm,
  setReranking,
  setLlmModel,
  setTemperature,

  transformOpts,
  searchAlgoOpts,
  rerankOpts,
  llmOpts,

  searchAlgoType,

  semanticTopK,
  semanticThreshold,
  keywordTopK,
  rerankerTopK,
  rerankerWeight,

  setSemanticTopK,
  setSemanticThreshold,
  setKeywordTopK,
  setRerankerTopK,
  setRerankerWeight,
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
              value={transformation}
              onChange={setTransformation}
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
          subtitle={
            searchAlgoType === 'hybrid'
              ? '시맨틱 + 키워드 + 리랭커 조합으로 관련 텍스트 청크를 검색합니다.'
              : '시맨틱 임베딩 기반으로 관련 텍스트 청크를 검색합니다.'
          }
          icon={PipelineIcons.Searching}
          onClick={scrollTo}
        />

        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="검색 알고리즘"
            hint={
              searchAlgoType === 'hybrid'
                ? '하이브리드(semantic + keyword + reranker) 전략을 사용합니다.'
                : '시맨틱 임베딩 기반 검색 전략을 사용합니다.'
            }
          />
          <div className="max-w-xs w-full">
            <Select
              value={searchAlgorithm}
              onChange={setSearchAlgorithm}
              options={searchAlgoOpts}
              disabled={loading || searchAlgoOpts.length === 0}
            />
          </div>
        </div>

        {searchAlgoType === 'hybrid' ? (
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border bg-white p-4">
              <p className="mb-2 text-sm font-semibold text-gray-900">
                시맨틱
                <span className="ml-1 text-[11px] font-normal text-gray-500">
                  의미 기반 임베딩 검색
                </span>
              </p>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-700">TopK</label>
                  <input
                    type="number"
                    min={1}
                    value={semanticTopK}
                    onChange={(e) => setSemanticTopK(Math.max(1, Number(e.target.value) || 1))}
                    disabled={loading}
                    className="w-full rounded-md border border-gray-200 px-3 py-2 text-right text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-700">
                    유사도 임계값
                  </label>
                  <div className="flex items-center gap-3">
                    <div className="w-full">
                      <Slider
                        value={semanticThreshold}
                        min={0}
                        max={1}
                        step={0.05}
                        onChange={setSemanticThreshold}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border bg-white p-4">
              <p className="mb-2 text-sm font-semibold text-gray-900">
                키워드
                <span className="ml-1 text-[11px] font-normal text-gray-500">키워드 기반 검색</span>
              </p>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-700">TopK</label>
                  <input
                    type="number"
                    min={1}
                    value={keywordTopK}
                    onChange={(e) => setKeywordTopK(Math.max(1, Number(e.target.value) || 1))}
                    disabled={loading}
                    className="w-full rounded-md border border-gray-200 px-3 py-2 text-right text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border bg-white p-4">
              <p className="mb-2 text-sm font-semibold text-gray-900">
                Reranker
                <span className="ml-1 text-[11px] font-normal text-gray-500">상위 후보 재정렬</span>
              </p>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-700">TopK</label>
                  <input
                    type="number"
                    min={1}
                    value={rerankerTopK}
                    onChange={(e) => setRerankerTopK(Math.max(1, Number(e.target.value) || 1))}
                    disabled={loading}
                    className="w-full rounded-md border border-gray-200 px-3 py-2 text-right text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-700">가중치</label>
                  <div className="flex items-center gap-3">
                    <div className="w-full">
                      <Slider
                        value={rerankerWeight}
                        min={0}
                        max={1}
                        step={0.05}
                        onChange={setRerankerWeight}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between gap-4">
              <LabelRow label="TopK" hint="쿼리와 가장 유사한 시맨틱 후보 개수입니다." />
              <div className="max-w-xs w-full">
                <input
                  type="number"
                  min={1}
                  value={semanticTopK}
                  onChange={(e) => setSemanticTopK(Math.max(1, Number(e.target.value) || 1))}
                  disabled={loading}
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent text-right"
                />
              </div>
            </div>

            <div className="flex items-center justify-between gap-4">
              <LabelRow
                label="유사도 임계값"
                hint="시맨틱 검색 결과 필터링에 사용할 유사도 임계값입니다."
              />
              <div className="max-w-sm w-full flex items-center gap-3">
                <div className="w-full">
                  <Slider
                    value={semanticThreshold}
                    min={0}
                    max={1}
                    step={0.05}
                    onChange={setSemanticThreshold}
                  />
                </div>
              </div>
            </div>
          </>
        )}
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
        <PromptManager />
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
            <Slider value={temperature} min={0} max={1} step={0.05} onChange={setTemperature} />
          </div>
        </div>
      </div>
    </>
  );
}
