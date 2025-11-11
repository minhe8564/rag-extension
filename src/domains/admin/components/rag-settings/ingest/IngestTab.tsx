import { useEffect, useMemo, useState } from 'react';
import type { Option } from '@/shared/components/Select';
import { IngestSettingsForm } from '@/domains/admin/components/rag-settings/ingest/IngestSettingsForm';
import TemplateList from '@/domains/admin/components/rag-settings/TemplateList';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

import {
  getIngestTemplates,
  getIngestTemplateDetail,
  createIngestTemplate,
  patchIngestTemplate,
  mapIngestTemplatesToOptions,
} from '@/domains/admin/api/rag-settings/ingest-templates.api';
import type { IngestTemplateDetailResult } from '@/domains/admin/types/rag-settings/templates.types';
import { isChunkingParams, num } from '@/domains/admin/utils/ragParsers';

export type IngestPreset = {
  template: string;
  extractEngine: string;
  chunkStrategy: string;
  chunkSize: number;
  overlap: number;
  embedModel: string;
  embedSparse: string;
  embedBackup: string;
};

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

  useEffect(() => {
    const run = async () => {
      setTplLoading(true);
      try {
        const list = await getIngestTemplates({ pageNum: 1, pageSize: 100 });
        setTplOpts(mapIngestTemplatesToOptions(list.data ?? []));
        const def =
          (list.data ?? []).find((t) => t.isDefault)?.ingestNo ??
          (list.data ?? [])[0]?.ingestNo ??
          '';
        if (!templateId && def) setTemplateId(def);
      } finally {
        setTplLoading(false);
      }
    };
    void run();
  }, [templateId]);

  useEffect(() => {
    const apply = (d: IngestTemplateDetailResult) => {
      const extractEngine = d.extractions?.[0]?.no ?? '';
      const chunkStrategy = d.chunking?.no ?? '';
      const embedModel = d.denseEmbeddings?.[0]?.no ?? '';
      const embedBackup = d.denseEmbeddings?.[1]?.no ?? d.denseEmbeddings?.[0]?.no ?? '';
      const embedSparse = d.sparseEmbedding?.no ?? '';
      let chunkSize = 512;
      let overlap = 40;
      if (isChunkingParams(d.chunking?.parameters)) {
        chunkSize = num(d.chunking.parameters?.token, chunkSize);
        overlap = num(d.chunking.parameters?.overlap, overlap);
      }
      setPreset({
        template: templateId,
        extractEngine,
        chunkStrategy,
        chunkSize,
        overlap,
        embedModel,
        embedSparse,
        embedBackup,
      });
    };

    const run = async () => {
      if (!templateId || isCreateMode) {
        setPreset(null);
        return;
      }
      const d = await getIngestTemplateDetail(templateId);
      apply(d);
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
    embedBackup: string;
    isCreateMode?: boolean;
  }) => {
    const dto = {
      name: payload.templateName,
      extractions: payload.extractEngine ? [{ no: payload.extractEngine }] : [],
      chunking: {
        no: payload.chunkStrategy,
        parameters: { token: payload.chunkSize, overlap: payload.overlap },
      },
      denseEmbeddings: [
        ...(payload.embedModel ? [{ no: payload.embedModel }] : []),
        ...(payload.embedBackup && payload.embedBackup !== payload.embedModel
          ? [{ no: payload.embedBackup }]
          : []),
      ],
      sparseEmbedding: payload.embedSparse ? { no: payload.embedSparse } : undefined,
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

      const extractEngine = detail.extractions?.[0]?.no ?? '';
      const chunkStrategy = detail.chunking?.no ?? '';
      const embedModel = detail.denseEmbeddings?.[0]?.no ?? '';
      const embedBackup = detail.denseEmbeddings?.[1]?.no ?? detail.denseEmbeddings?.[0]?.no ?? '';
      const embedSparse = detail.sparseEmbedding?.no ?? '';
      let chunkSize = 512;
      let overlap = 40;
      if (isChunkingParams(detail.chunking?.parameters)) {
        chunkSize = num(detail.chunking.parameters?.token, chunkSize);
        overlap = num(detail.chunking.parameters?.overlap, overlap);
      }
      setPreset({
        template: created.ingestNo,
        extractEngine,
        chunkStrategy,
        chunkSize,
        overlap,
        embedModel,
        embedSparse,
        embedBackup,
      });
      onCreate?.();
      return;
    }

    // console.log('patchIngestTemplate', payload.template, dto);
    await patchIngestTemplate(payload.template, dto);

    const [detail, list] = await Promise.all([
      getIngestTemplateDetail(payload.template),
      getIngestTemplates({ pageNum: 1, pageSize: 100 }),
    ]);

    {
      const extractEngine = detail.extractions?.[0]?.no ?? '';
      const chunkStrategy = detail.chunking?.no ?? '';
      const embedModel = detail.denseEmbeddings?.[0]?.no ?? '';
      const embedBackup = detail.denseEmbeddings?.[1]?.no ?? detail.denseEmbeddings?.[0]?.no ?? '';
      const embedSparse = detail.sparseEmbedding?.no ?? '';
      let chunkSize = 512;
      let overlap = 40;
      if (isChunkingParams(detail.chunking?.parameters)) {
        chunkSize = num(detail.chunking.parameters?.token, chunkSize);
        overlap = num(detail.chunking.parameters?.overlap, overlap);
      }
      setPreset({
        template: payload.template,
        extractEngine,
        chunkStrategy,
        chunkSize,
        overlap,
        embedModel,
        embedSparse,
        embedBackup,
      });
    }

    setTplOpts(mapIngestTemplatesToOptions(list.data ?? []));
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
        />
      </div>

      <aside className="space-y-4">
        <TemplateList
          kind="ingest"
          active={templateId}
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
        />
      </aside>
    </section>
  );
}
