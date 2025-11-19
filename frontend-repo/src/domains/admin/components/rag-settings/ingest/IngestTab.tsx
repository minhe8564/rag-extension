import { useEffect, useMemo, useRef, useState } from 'react';
import type { Option } from '@/shared/components/controls/Select';
import { IngestSettingsForm } from '@/domains/admin/components/rag-settings/ingest/IngestSettingsForm';
import TemplateList from '@/domains/admin/components/rag-settings/TemplateList';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

import {
  getIngestTemplates,
  getIngestTemplateDetail,
  createIngestTemplate,
  putIngestTemplate,
  mapIngestTemplatesToOptions,
} from '@/domains/admin/api/rag-settings/ingest-templates.api';
import type { IngestTemplateDetailResult } from '@/domains/admin/types/rag-settings/templates.types';
import { isChunkingParams, num } from '@/domains/admin/utils/ragParsers';
import type { IngestPreset } from '@/domains/admin/types/rag-settings/ingest/ingestSettings.types';

type Props = {
  anchors: Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;
  ragOptions: RagOptions | null;
  optionsLoading: boolean;
  onRequestDelete: (id: string) => void;
  onCreate: () => void;
};

export default function IngestTab({
  anchors,
  ragOptions,
  optionsLoading,
  onRequestDelete,
  onCreate,
}: Props) {
  const [templateId, setTemplateId] = useState('');
  const [tplOpts, setTplOpts] = useState<Option[]>([]);
  const [tplLoading, setTplLoading] = useState(false);
  const [preset, setPreset] = useState<IngestPreset | null>(null);
  const [isCreateMode, setIsCreateMode] = useState(false);
  const [hasDirtyChanges, setHasDirtyChanges] = useState(false);

  const saveRef = useRef<(() => void | Promise<void>) | null>(null);

  useEffect(() => {
    const run = async () => {
      setTplLoading(true);
      try {
        const list = await getIngestTemplates({ pageNum: 1, pageSize: 100 });
        const data = list.data ?? [];
        setTplOpts(mapIngestTemplatesToOptions(data));
        const def = data.find((t) => t.isDefault)?.ingestNo ?? data[0]?.ingestNo ?? '';
        if (!isCreateMode && !templateId && def) setTemplateId(def);
      } finally {
        setTplLoading(false);
      }
    };
    void run();
  }, [templateId, isCreateMode]);

  const applyDetailToPreset = (d: IngestTemplateDetailResult, id: string) => {
    const extractEngine = d.extractions?.[0]?.no ?? '';
    const chunkStrategy = d.chunking?.no ?? '';
    const embedModel = d.denseEmbeddings?.[0]?.no ?? '';
    const embedSparse = d.sparseEmbedding?.no ?? '';
    let chunkSize = 512;
    let overlap = 40;
    if (isChunkingParams(d.chunking?.parameters)) {
      chunkSize = num(d.chunking.parameters?.token, chunkSize);
      overlap = num(d.chunking.parameters?.overlap, overlap);
    }

    const nextPreset: IngestPreset = {
      template: id,
      extractEngine,
      chunkStrategy,
      chunkSize,
      overlap,
      embedModel,
      embedSparse,
      isDefault: !!d.isDefault,
    };

    setPreset(nextPreset);
  };

  useEffect(() => {
    const run = async () => {
      if (!templateId || isCreateMode) {
        setPreset(null);
        return;
      }
      const detail = await getIngestTemplateDetail(templateId);
      applyDetailToPreset(detail, templateId);
    };
    void run();
  }, [templateId, isCreateMode]);

  const mergedOptions: RagOptions | null = useMemo(
    () => (ragOptions ? { ...ragOptions, ingestTemplate: tplOpts } : null),
    [ragOptions, tplOpts]
  );

  const handleCreateNew = () => {
    setIsCreateMode(true);
    setTemplateId('');
    setPreset(null);
  };

  const handleIngestSave = async (payload: {
    template: string;
    templateName: string;
    extractEngine: string;
    chunkStrategy: string;
    chunkSize: number;
    overlap: number;
    embedModel: string;
    embedSparse: string;
    isDefault: boolean;
    isCreateMode?: boolean;
  }) => {
    const dto = {
      name: payload.templateName,
      extractions: payload.extractEngine ? [{ no: payload.extractEngine }] : [],
      chunking: {
        no: payload.chunkStrategy,
        parameters: { token: payload.chunkSize, overlap: payload.overlap },
      },
      denseEmbeddings: payload.embedModel ? [{ no: payload.embedModel }] : [],
      sparseEmbedding: payload.embedSparse ? { no: payload.embedSparse } : undefined,
      isDefault: payload.isDefault,
    };

    if (isCreateMode) {
      const created = await createIngestTemplate(dto);
      const [detail, list] = await Promise.all([
        getIngestTemplateDetail(created.ingestNo),
        getIngestTemplates({ pageNum: 1, pageSize: 100 }),
      ]);
      setTplOpts(mapIngestTemplatesToOptions(list.data ?? []));
      setTemplateId(created.ingestNo);
      setIsCreateMode(false);
      applyDetailToPreset(detail, created.ingestNo);
      setHasDirtyChanges(false);
      onCreate?.();
      return;
    }

    await putIngestTemplate(payload.template, dto);
    const [detail, list] = await Promise.all([
      getIngestTemplateDetail(payload.template),
      getIngestTemplates({ pageNum: 1, pageSize: 100 }),
    ]);
    applyDetailToPreset(detail, payload.template);
    setTplOpts(mapIngestTemplatesToOptions(list.data ?? []));
    setHasDirtyChanges(false);
  };

  return (
    <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      <div>
        <div ref={anchors.extract} />
        <div ref={anchors.chunking} />
        <div ref={anchors.embedding} />

        <IngestSettingsForm
          template={templateId}
          isCreateMode={isCreateMode}
          options={mergedOptions ?? undefined}
          loading={optionsLoading || tplLoading}
          preset={preset ?? undefined}
          onSave={handleIngestSave}
          onDirtyChange={(dirty) => setHasDirtyChanges(dirty)}
          registerSaveHandler={(fn) => {
            saveRef.current = fn;
          }}
        />
      </div>

      <aside className="space-y-4 sticky top-20 h-fit">
        <TemplateList
          kind="ingest"
          active={templateId}
          activeIsDirty={!isCreateMode && !!templateId && hasDirtyChanges}
          onSelect={(id) => {
            setIsCreateMode(false);
            setTemplateId(id);
          }}
          onEdit={(id) => {
            setIsCreateMode(false);
            setTemplateId(id);
          }}
          onDelete={onRequestDelete}
          onCreate={handleCreateNew}
          onSaveActiveTemplate={() => {
            saveRef.current?.();
          }}
        />
      </aside>
    </section>
  );
}
