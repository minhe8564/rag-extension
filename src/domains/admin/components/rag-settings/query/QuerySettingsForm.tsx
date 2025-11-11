import { useEffect, useState } from 'react';
import type { Option } from '@/shared/components/Select';
import { Save } from 'lucide-react';
import { toast } from 'react-toastify';
import Tooltip from '@/shared/components/Tooltip';
import QuerySettingsFields from '@/domains/admin/components/rag-settings/query/QuerySettingsFields';
import type {
  SavePayload,
  QuerySettingsFormProps,
} from '@/domains/admin/types/rag-settings/query/querySettings.types';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

export function QuerySettingsForm({
  template,
  isCreateMode = false,
  onSave,
  options,
  loading = false,
  anchors,
  preset,
}: QuerySettingsFormProps) {
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

  const [baseline, setBaseline] = useState<Omit<SavePayload, 'isCreateMode' | 'template'>>({
    templateName: selectedTemplateLabel,
    queryEngine,
    searchAlgorithm,
    topK,
    threshold,
    reranking,
    llmModel,
    temperature,
    multimodal,
  });

  useEffect(() => {
    const ready =
      transformOpts.length || searchAlgoOpts.length || rerankOpts.length || llmOpts.length;
    if (!ready) return;

    const next = {
      queryEngine: safe(transformOpts, preset?.queryEngine),
      searchAlgorithm: safe(searchAlgoOpts, preset?.searchAlgorithm),
      topK: typeof preset?.topK === 'number' ? Math.max(1, preset.topK) : 5,
      threshold:
        typeof preset?.threshold === 'number' ? Math.min(1, Math.max(0, preset.threshold)) : 0.2,
      reranking: safe(rerankOpts, preset?.reranking),
      llmModel: safe(llmOpts, preset?.llmModel),
      temperature:
        typeof preset?.temperature === 'number'
          ? Math.min(1, Math.max(0, preset.temperature))
          : 0.2,
      multimodal: typeof preset?.multimodal === 'boolean' ? preset.multimodal : false,
    };

    setQueryEngine(next.queryEngine);
    setSearchAlgorithm(next.searchAlgorithm);
    setTopK(next.topK);
    setThreshold(next.threshold);
    setReranking(next.reranking);
    setLlmModel(next.llmModel);
    setTemperature(next.temperature);
    setMultimodal(next.multimodal);

    setBaseline({
      templateName: isCreateMode ? '' : selectedTemplateLabel,
      ...next,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    isCreateMode,
    preset,
    transformOpts.length,
    searchAlgoOpts.length,
    rerankOpts.length,
    llmOpts.length,
    selectedTemplateLabel,
  ]);

  const dirty = isCreateMode
    ? templateName.trim().length > 0
    : JSON.stringify({
        templateName,
        queryEngine,
        searchAlgorithm,
        topK,
        threshold,
        reranking,
        llmModel,
        temperature,
        multimodal,
      }) !== JSON.stringify(baseline);

  const scrollTo = (id: FlowStepId) =>
    anchors?.[id]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const handleSave = async () => {
    const payload: SavePayload = {
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
    };
    await onSave?.(payload);
    toast.success(isCreateMode ? '템플릿이 생성되었습니다.' : '설정이 저장되었습니다.');
    if (!isCreateMode) {
      setBaseline({
        templateName,
        queryEngine,
        searchAlgorithm,
        topK,
        threshold,
        reranking,
        llmModel,
        temperature,
        multimodal,
      });
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
      <span>{isCreateMode ? '생성' : '저장'}</span>
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

      <QuerySettingsFields
        anchors={anchors}
        loading={loading}
        scrollTo={scrollTo}
        // values
        queryEngine={queryEngine}
        searchAlgorithm={searchAlgorithm}
        topK={topK}
        threshold={threshold}
        reranking={reranking}
        llmModel={llmModel}
        temperature={temperature}
        multimodal={multimodal}
        // handlers
        setQueryEngine={setQueryEngine}
        setSearchAlgorithm={setSearchAlgorithm}
        setTopK={setTopK}
        setThreshold={setThreshold}
        setReranking={setReranking}
        setLlmModel={setLlmModel}
        setTemperature={setTemperature}
        setMultimodal={setMultimodal}
        // options
        transformOpts={transformOpts}
        searchAlgoOpts={searchAlgoOpts}
        rerankOpts={rerankOpts}
        llmOpts={llmOpts}
      />
    </div>
  );
}
