import { useEffect, useMemo, useRef, useState } from 'react';
import type { Option } from '@/shared/components/Select';
import { Save, Check } from 'lucide-react';
import { toast } from 'react-toastify';
import Tooltip from '@/shared/components/Tooltip';
import IngestSettingsFields from '@/domains/admin/components/rag-settings/ingest/IngestSettingsFields';
import type {
  SavePayload,
  IngestSettingsFormProps,
} from '@/domains/admin/types/rag-settings/ingest/ingestSettings.types';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';
import clsx from 'clsx';
import { useQueryClient } from '@tanstack/react-query';

export function IngestSettingsForm({
  template,
  isCreateMode = false,
  onSave,
  options,
  loading = false,
  anchors,
  preset,
}: IngestSettingsFormProps) {
  const queryClient = useQueryClient();
  const templateOpts: Option[] = options?.ingestTemplate ?? [];
  const extractOpts: Option[] = options?.extract ?? [];
  const chunkOpts: Option[] = options?.chunk ?? [];
  const embedDenseOpts: Option[] = options?.embedDense ?? [];
  const embedSparseOpts: Option[] = options?.embedSparse ?? [];

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
  const [isDefault, setIsDefault] = useState<boolean>(!!preset?.isDefault);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTemplateName(isCreateMode ? '' : selectedTemplateLabel);
  }, [isCreateMode, selectedTemplateLabel, template]);

  const [baseline, setBaseline] = useState<Omit<SavePayload, 'isCreateMode' | 'template'>>({
    templateName: selectedTemplateLabel,
    extractEngine,
    chunkStrategy,
    chunkSize,
    overlap,
    embedModel,
    embedSparse,
    isDefault,
  });

  useEffect(() => {
    if (!extractOpts.length && !chunkOpts.length && !embedDenseOpts.length) return;

    const next = {
      extractEngine: safe(extractOpts, preset?.extractEngine),
      chunkStrategy: safe(chunkOpts, preset?.chunkStrategy),
      chunkSize: typeof preset?.chunkSize === 'number' ? preset!.chunkSize : 512,
      overlap: typeof preset?.overlap === 'number' ? preset!.overlap : 40,
      embedModel: safe(embedDenseOpts, preset?.embedModel),
      embedSparse: safe(embedSparseOpts, preset?.embedSparse),
      isDefault: !!preset?.isDefault,
    };

    setExtractEngine(next.extractEngine);
    setChunkStrategy(next.chunkStrategy);
    setChunkSize(next.chunkSize);
    setOverlap(next.overlap);
    setEmbedModel(next.embedModel);
    setEmbedSparse(next.embedSparse);
    setIsDefault(next.isDefault);

    setBaseline({
      templateName: isCreateMode ? '' : selectedTemplateLabel,
      ...next,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    template,
    isCreateMode,
    preset,
    extractOpts.length,
    chunkOpts.length,
    embedDenseOpts.length,
    embedSparseOpts.length,
  ]);

  const dirty = useMemo(() => {
    const current = {
      templateName,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      isDefault,
    };
    return isCreateMode
      ? templateName.trim().length > 0
      : JSON.stringify(current) !== JSON.stringify(baseline);
  }, [
    isCreateMode,
    templateName,
    extractEngine,
    chunkStrategy,
    chunkSize,
    overlap,
    embedModel,
    embedSparse,
    isDefault,
    baseline,
  ]);

  const scrollTo = (id: FlowStepId) => {
    anchors?.[id]?.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  };

  const invalidateAllIngestQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['admin', 'ragSettings', 'ingest', 'templates'] }),
      queryClient.invalidateQueries({ queryKey: ['admin', 'ragSettings', 'ingest', 'current'] }),
      queryClient.invalidateQueries({
        queryKey: ['admin', 'ragSettings', 'ingest', 'detail', template],
      }),
    ]);
  };

  const handleSave = async () => {
    const payload: SavePayload = {
      template,
      templateName,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      isDefault,
      isCreateMode,
    };

    setSaving(true);
    await onSave?.(payload);
    await invalidateAllIngestQueries();

    setBaseline({
      templateName,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      isDefault,
    });

    toast.success(isCreateMode ? '템플릿이 생성되었습니다.' : '설정이 저장되었습니다.');
    setSaved(true);
    setTimeout(() => setSaved(false), 900);
    setSaving(false);
  };

  const SaveBtn = (
    <button
      type="button"
      onClick={handleSave}
      disabled={loading || saving || !dirty}
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-all',
        'disabled:cursor-not-allowed disabled:opacity-60',
        dirty && !loading && !saving
          ? 'bg-[var(--color-hebees)] text-white border-[var(--color-hebees)] hover:opacity-90'
          : 'bg-white text-gray-700 border hover:bg-gray-50'
      )}
    >
      {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
      <span>{saving ? '처리 중…' : saved ? '저장됨' : isCreateMode ? '생성' : '저장'}</span>
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

        <div className="flex flex-wrap items-center gap-4">
          <div className="max-w-xs w-full">
            <input
              ref={nameInputRef}
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

          <Tooltip content="이 템플릿을 기본값으로 사용합니다." side="bottom">
            <button
              type="button"
              onClick={() => setIsDefault((v) => !v)}
              aria-pressed={isDefault}
              className={clsx(
                'inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition',
                isDefault
                  ? 'border-[var(--color-hebees)] bg-[var(--color-hebees-bg)] text-[var(--color-hebees)]'
                  : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
              )}
            >
              <span
                className={clsx(
                  'inline-flex h-4 w-7 items-center rounded-full transition',
                  isDefault ? 'bg-[var(--color-hebees)]' : 'bg-gray-300'
                )}
              >
                <span
                  className={clsx(
                    'ml-[2px] h-3.5 w-3.5 rounded-full bg-white transition',
                    isDefault ? 'translate-x-[10px]' : 'translate-x-0'
                  )}
                />
              </span>
              기본 템플릿
            </button>
          </Tooltip>

          {!dirty ? (
            <Tooltip content="변경된 값이 있을 경우 활성화 됩니다." side="bottom">
              <div className="inline-flex">{SaveBtn}</div>
            </Tooltip>
          ) : (
            SaveBtn
          )}
        </div>
      </div>

      <IngestSettingsFields
        anchors={anchors}
        loading={loading || saving}
        scrollTo={scrollTo}
        // values
        extractEngine={extractEngine}
        chunkStrategy={chunkStrategy}
        chunkSize={chunkSize}
        overlap={overlap}
        embedModel={embedModel}
        embedSparse={embedSparse}
        // handlers
        setExtractEngine={setExtractEngine}
        setChunkStrategy={setChunkStrategy}
        setChunkSize={setChunkSize}
        setOverlap={setOverlap}
        setEmbedModel={setEmbedModel}
        setEmbedSparse={setEmbedSparse}
        // options
        extractOpts={extractOpts}
        chunkOpts={chunkOpts}
        embedDenseOpts={embedDenseOpts}
        embedSparseOpts={embedSparseOpts}
      />
    </div>
  );
}
