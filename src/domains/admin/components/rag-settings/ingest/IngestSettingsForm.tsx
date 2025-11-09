import { useEffect, useMemo, useState } from 'react';
import Select, { type Option } from '@/shared/components/Select';
import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { Save } from 'lucide-react';
import { toast } from 'react-toastify';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';
import SectionHeader from '@/domains/admin/components/rag-settings/ui/SectionHeader';
import Tooltip from '@/shared/components/Tooltip';

type SavePayload = {
  template: string;
  templateName: string;
  extractEngine: string;
  chunkStrategy: string;
  chunkSize: number;
  overlap: number;
  embedModel: string;
  embedSparse: string;
  embedBackup: string;
  isCreateMode?: boolean;
};

export type IngestPreset = {
  extractEngine?: string;
  chunkStrategy?: string;
  chunkSize?: number;
  overlap?: number;
  embedModel?: string;
  embedSparse?: string;
  embedBackup?: string;
};

export function IngestSettingsForm({
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
  preset?: IngestPreset;
}) {
  const templateOpts: Option[] = options?.ingestTemplate ?? [];
  const extractOpts: Option[] = options?.extract ?? [];
  const chunkOpts: Option[] = options?.chunk ?? [];
  const embedDenseOpts: Option[] = options?.embedDense ?? [];
  const embedSparseOpts: Option[] = options?.embedSparse ?? [];
  const embedBackupOpts: Option[] = embedDenseOpts;

  const selectedTemplateLabel =
    templateOpts.find((o) => o.value === template)?.label ?? '템플릿 없음';

  const safe = (opts: Option[], v?: string) =>
    v && opts.some((o) => o.value === v) ? v : (opts[0]?.value ?? '');

  const [templateName, setTemplateName] = useState(isCreateMode ? '' : selectedTemplateLabel);
  const [extractEngine, setExtractEngine] = useState(safe(extractOpts));
  const [chunkStrategy, setChunkStrategy] = useState(safe(chunkOpts));
  const [chunkSize, setChunkSize] = useState(512);
  const [overlap, setOverlap] = useState(40);
  const [embedModel, setEmbedModel] = useState(safe(embedDenseOpts));
  const [embedSparse, setEmbedSparse] = useState(safe(embedSparseOpts));
  const [embedBackup, setEmbedBackup] = useState(safe(embedBackupOpts));

  useEffect(() => {
    setTemplateName(isCreateMode ? '' : selectedTemplateLabel);
  }, [isCreateMode, selectedTemplateLabel, template]);

  const [baseline, setBaseline] = useState<SavePayload | null>(null);

  const currentPayload = useMemo<SavePayload>(
    () => ({
      template,
      templateName,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      embedBackup,
      isCreateMode,
    }),
    [
      template,
      templateName,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      embedBackup,
      isCreateMode,
    ]
  );

  const toComparable = (p: SavePayload) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
    if (!extractOpts.length && !chunkOpts.length && !embedDenseOpts.length) return;

    const next = {
      extractEngine: safe(extractOpts, preset?.extractEngine ?? extractEngine),
      chunkStrategy: safe(chunkOpts, preset?.chunkStrategy ?? chunkStrategy),
      chunkSize: typeof preset?.chunkSize === 'number' ? preset!.chunkSize : chunkSize,
      overlap: typeof preset?.overlap === 'number' ? preset!.overlap : overlap,
      embedModel: safe(embedDenseOpts, preset?.embedModel ?? embedModel),
      embedSparse: safe(embedSparseOpts, preset?.embedSparse ?? embedSparse),
      embedBackup: safe(embedBackupOpts, preset?.embedBackup ?? embedBackup),
    };

    setExtractEngine(next.extractEngine);
    setChunkStrategy(next.chunkStrategy);
    setChunkSize(next.chunkSize);
    setOverlap(next.overlap);
    setEmbedModel(next.embedModel);
    setEmbedSparse(next.embedSparse);
    setEmbedBackup(next.embedBackup);

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
    extractOpts.length,
    chunkOpts.length,
    embedDenseOpts.length,
    embedSparseOpts.length,
    embedBackupOpts.length,
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
          <h3 className="text-lg font-semibold text-gray-900">Ingest 파이프라인 템플릿</h3>
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

      <div ref={anchors?.extract} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="extract"
          title="Extract · 문서 수집"
          subtitle="문서에서 텍스트·이미지·표를 추출하는 방법을 선택합니다."
          icon={PipelineIcons.Extract}
          onClick={scrollTo}
        />
        <div className="flex items-center justify-between gap-4">
          <LabelRow label="추출 엔진 선택" hint="PDF/이미지 등 입력 형식에 맞는 엔진을 고르세요." />
          <div className="max-w-xs w-full">
            <Select
              value={extractEngine}
              onChange={setExtractEngine}
              options={extractOpts}
              disabled={loading || extractOpts.length === 0}
            />
          </div>
        </div>
      </div>

      <div ref={anchors?.chunking} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="chunking"
          title="Chunking · 문서 분할"
          subtitle="문서를 의미 단위로 나누어 처리 효율을 높입니다."
          icon={PipelineIcons.Chunking}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="청킹 전략 선택" hint="문서를 나누는 기준을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select
              value={chunkStrategy}
              onChange={setChunkStrategy}
              options={chunkOpts}
              disabled={loading || chunkOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="청크 크기"
            hint="큰 청크는 더 많은 컨텍스트를, 작은 청크는 더 높은 정밀도를 제공합니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={chunkSize} min={1} max={512} onChange={setChunkSize} />
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="오버랩 토큰 수"
            hint="오버랩이 클수록 문맥 연속성은 좋아지지만 중복이 증가합니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={overlap} min={0} max={200} step={1} onChange={setOverlap} />
          </div>
        </div>
      </div>

      <div ref={anchors?.embedding} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="embedding"
          title="Embedding · 벡터화"
          subtitle="분할된 문서를 벡터로 변환합니다. Dense/Sparse를 함께 구성할 수 있어요."
          icon={PipelineIcons.Embedding}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="임베딩 모델 (Dense)"
            hint="텍스트를 벡터로 변환할 기본 임베딩 모델입니다."
          />
          <div className="max-w-sm w-full">
            <Select
              value={embedModel}
              onChange={setEmbedModel}
              options={embedDenseOpts}
              disabled={loading || embedDenseOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="임베딩 모델 (Sparse)"
            hint="희소 벡터 기반 임베딩(예: SPLADE). 하이브리드 검색에 유리합니다."
          />
          <div className="max-w-sm w-full">
            <Select
              value={embedSparse}
              onChange={setEmbedSparse}
              options={embedSparseOpts}
              disabled={loading || embedSparseOpts.length === 0}
            />
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="추가 임베딩 모델 (Dense)"
            hint="보조 임베딩 모델을 설정해 도메인 적응력을 높일 수 있습니다."
          />
          <div className="max-w-sm w-full">
            <Select
              value={embedBackup}
              onChange={setEmbedBackup}
              options={embedBackupOpts}
              disabled={loading || embedBackupOpts.length === 0}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
