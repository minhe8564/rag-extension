import { useEffect, useState } from 'react';
import type { Option } from '@/shared/components/Select';
import { Save } from 'lucide-react';
import { toast } from 'react-toastify';
import Tooltip from '@/shared/components/Tooltip';
import IngestSettingsFields from '@/domains/admin/components/rag-settings/ingest/IngestSettingsFields';
import type {
  SavePayload,
  IngestSettingsFormProps,
} from '@/domains/admin/types/rag-settings/ingest/ingestSettings.types';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

export function IngestSettingsForm({
  template,
  isCreateMode = false,
  onSave,
  options,
  loading = false,
  anchors,
  preset,
}: IngestSettingsFormProps) {
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

  const [baseline, setBaseline] = useState<Omit<SavePayload, 'isCreateMode' | 'template'>>({
    templateName: selectedTemplateLabel,
    extractEngine,
    chunkStrategy,
    chunkSize,
    overlap,
    embedModel,
    embedSparse,
    embedBackup,
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
      embedBackup: safe(embedBackupOpts, preset?.embedBackup),
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
        templateName: selectedTemplateLabel,
        ...next,
      });
    } else {
      setBaseline({
        templateName: '',
        ...next,
      });
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

  const dirty = isCreateMode
    ? templateName.trim().length > 0
    : JSON.stringify({
        templateName,
        extractEngine,
        chunkStrategy,
        chunkSize,
        overlap,
        embedModel,
        embedSparse,
        embedBackup,
      }) !== JSON.stringify(baseline);

  const scrollTo = (id: FlowStepId) => {
    anchors?.[id]?.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
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
      embedBackup,
      isCreateMode,
    };
    await onSave?.(payload);
    toast.success(isCreateMode ? '템플릿이 생성되었습니다.' : '설정이 저장되었습니다.');
    if (!isCreateMode) {
      setBaseline({
        templateName,
        extractEngine,
        chunkStrategy,
        chunkSize,
        overlap,
        embedModel,
        embedSparse,
        embedBackup,
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

      <IngestSettingsFields
        anchors={anchors}
        loading={loading}
        scrollTo={scrollTo}
        // values
        extractEngine={extractEngine}
        chunkStrategy={chunkStrategy}
        chunkSize={chunkSize}
        overlap={overlap}
        embedModel={embedModel}
        embedSparse={embedSparse}
        embedBackup={embedBackup}
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
