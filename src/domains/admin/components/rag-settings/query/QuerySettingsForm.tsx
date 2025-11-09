import { useEffect, useMemo, useState } from 'react';
import Select, { type Option } from '@/shared/components/Select';
import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { Toggle } from '@/domains/admin/components/rag-settings/ui/Toggle';
import PromptManager from '@/domains/admin/components/rag-settings/query/PromptManager';
import Tooltip from '@/shared/components/Tooltip';
import { Save } from 'lucide-react';
import { toast } from 'react-toastify';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';
import SectionHeader from '@/domains/admin/components/rag-settings/ui/SectionHeader';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';

type SavePayload = {
  template: string;
  templateName: string;
  queryEngine: string;
  searchAlgorithm: string;
  topK: number;
  threshold: number;
  reranking: string;
  llmModel: string;
  temperature: number;
  multimodal: boolean;
  isCreateMode?: boolean;
};

export type QueryPreset = Partial<
  Pick<
    SavePayload,
    | 'queryEngine'
    | 'searchAlgorithm'
    | 'topK'
    | 'threshold'
    | 'reranking'
    | 'llmModel'
    | 'temperature'
    | 'multimodal'
  >
>;

export function QuerySettingsForm({
  template,
  isCreateMode = false,
  onSave,
  options,
  loading = false,
  anchors,
  preset,
}: {
  template: string;
  isCreateMode?: boolean;
  onSave?: (payload: SavePayload) => void | Promise<void>;
  options?: RagOptions | null;
  loading?: boolean;
  anchors?: Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;
  preset?: QueryPreset;
}) {
  const templateOpts: Option[] = options?.queryTemplate ?? [];
  const transformOpts: Option[] = options?.transform ?? [];
  const searchAlgoOpts: Option[] = [
    ...(options?.searchSemantic ?? []),
    ...(options?.searchHybrid ?? []),
  ];
  const rerankOpts: Option[] = options?.rerank ?? [];
  const llmOpts: Option[] = options?.generation ?? [];

  const selectedTemplateLabel =
    templateOpts.find((o) => o.value === template)?.label ?? '템플릿 없음';

  const safe = (opts: Option[], v?: string) =>
    v && opts.some((o) => o.value === v) ? v : (opts[0]?.value ?? '');

  const [templateName, setTemplateName] = useState(isCreateMode ? '' : selectedTemplateLabel);
  const [queryEngine, setQueryEngine] = useState(safe(transformOpts));
  const [searchAlgorithm, setSearchAlgorithm] = useState(safe(searchAlgoOpts));
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.2);
  const [reranking, setReranking] = useState(safe(rerankOpts));
  const [llmModel, setLlmModel] = useState(safe(llmOpts));
  const [temperature, setTemperature] = useState(0.2);
  const [multimodal, setMultimodal] = useState(false);

  useEffect(() => {
    setTemplateName(isCreateMode ? '' : selectedTemplateLabel);
  }, [isCreateMode, selectedTemplateLabel, template]);

  const [baseline, setBaseline] = useState<SavePayload | null>(null);

  const currentPayload = useMemo<SavePayload>(
    () => ({
      template,
      templateName,
      queryEngine,
      searchAlgorithm,
      topK,
      threshold,
      reranking,
      llmModel,
      temperature,
      multimodal,
      isCreateMode,
    }),
    [
      template,
      templateName,
      queryEngine,
      searchAlgorithm,
      topK,
      threshold,
      reranking,
      llmModel,
      temperature,
      multimodal,
      isCreateMode,
    ]
  );

  const toComparable = (p: SavePayload) => {
    const { isCreateMode: _omit, ...rest } = p;
    return rest;
  };

  const dirty = useMemo(() => {
    if (isCreateMode) return templateName.trim().length > 0;
    return baseline
      ? JSON.stringify(toComparable(baseline)) !== JSON.stringify(toComparable(currentPayload))
      : false;
  }, [isCreateMode, templateName, baseline, currentPayload]);

  useEffect(() => {
    const ready =
      transformOpts.length || searchAlgoOpts.length || rerankOpts.length || llmOpts.length;
    if (!ready) return;

    const next = {
      queryEngine: safe(transformOpts, preset?.queryEngine ?? queryEngine),
      searchAlgorithm: safe(searchAlgoOpts, preset?.searchAlgorithm ?? searchAlgorithm),
      topK: typeof preset?.topK === 'number' ? Math.max(1, preset.topK) : topK,
      threshold:
        typeof preset?.threshold === 'number'
          ? Math.min(1, Math.max(0, preset.threshold))
          : threshold,
      reranking: safe(rerankOpts, preset?.reranking ?? reranking),
      llmModel: safe(llmOpts, preset?.llmModel ?? llmModel),
      temperature:
        typeof preset?.temperature === 'number'
          ? Math.min(1, Math.max(0, preset.temperature))
          : temperature,
      multimodal: typeof preset?.multimodal === 'boolean' ? preset.multimodal : multimodal,
    };

    setQueryEngine(next.queryEngine);
    setSearchAlgorithm(next.searchAlgorithm);
    setTopK(next.topK);
    setThreshold(next.threshold);
    setReranking(next.reranking);
    setLlmModel(next.llmModel);
    setTemperature(next.temperature);
    setMultimodal(next.multimodal);

    if (!isCreateMode) {
      setBaseline({
        template,
        templateName: selectedTemplateLabel,
        ...next,
        isCreateMode: false,
      });
    } else {
      setBaseline(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    template,
    isCreateMode,
    preset,
    transformOpts.length,
    searchAlgoOpts.length,
    rerankOpts.length,
    llmOpts.length,
  ]);

  const scrollTo = (id: FlowStepId) =>
    anchors?.[id]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const handleSave = async () => {
    try {
      await onSave?.(currentPayload);
      toast.success(isCreateMode ? '템플릿이 생성되었습니다.' : '설정이 저장되었습니다.');
      if (!isCreateMode) setBaseline(currentPayload);
    } catch {
      toast.error('설정 저장에 실패했습니다.');
    }
  };

  const SaveBtn = (
    <button
      type="button"
      onClick={handleSave}
      disabled={loading || !dirty}
      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors
      disabled:cursor-not-allowed disabled:opacity-60
      ${
        dirty && !loading
          ? 'bg-[var(--color-hebees)] text-white border-[var(--color-hebees)] hover:opacity-90'
          : 'bg-white text-gray-700 border hover:bg-gray-50'
      }`}
    >
      <Save className="h-4 w-4" />
      {isCreateMode ? '생성' : '저장'}
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border bg-white p-8 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Query 파이프라인 템플릿</h3>
          <p className="mt-2 inline-flex items-center gap-2 rounded-md bg-[var(--color-hebees-bg)] px-3 py-1 text-sm font-normal text-[var(--color-hebees)]">
            <span className="font-bold">TIP</span>
            자주 사용하는 설정을 템플릿으로 저장해 빠르게 불러올 수 있어요.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="max-w-xs w-full">
            <input
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder={isCreateMode ? '새 템플릿 이름 입력' : '템플릿 이름 입력'}
              className="
                w-full rounded-lg px-3 py-2 text-base bg-white text-gray-900
                border-gray-200 focus:border-[var(--color-hebees)] focus:bg-[var(--color-hebees-bg)] focus:ring-0 focus:outline-none
                placeholder:text-gray-400
              "
            />
          </div>

          {!dirty ? (
            <Tooltip content="변경된 값이 있을 경우 활성화 됩니다." side="bottom">
              <div className="inline-flex">{SaveBtn}</div>
            </Tooltip>
          ) : (
            SaveBtn
          )}
        </div>
      </div>

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
    </div>
  );
}
