import { useEffect, useMemo, useRef, useState } from 'react';
import type { Option } from '@/shared/components/controls/Select';
import { QuerySettingsForm } from '@/domains/admin/components/rag-settings/query/QuerySettingsForm';
import TemplateList from '@/domains/admin/components/rag-settings/TemplateList';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

import {
  getQueryTemplates,
  getQueryTemplateDetail,
  putQueryTemplate,
  mapQueryTemplatesToOptions,
  createQueryTemplate,
} from '@/domains/admin/api/rag-settings/query-templates.api';
import type { QueryTemplateDetailResult } from '@/domains/admin/types/rag-settings/templates.types';
import {
  bool,
  isGenerationParams,
  isHybridParams,
  isSemanticParams,
  num,
} from '@/domains/admin/utils/ragParsers';
import type { QueryPreset } from '@/domains/admin/types/rag-settings/query/querySettings.types';

type Props = {
  anchors: Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;
  ragOptions: RagOptions | null;
  optionsLoading: boolean;
  onRequestDelete: (id: string) => void;
  onCreate: () => void;
};

export default function QueryTab({
  anchors,
  ragOptions,
  optionsLoading,
  onRequestDelete,
  onCreate,
}: Props) {
  const [templateId, setTemplateId] = useState('');
  const [tplOpts, setTplOpts] = useState<Option[]>([]);
  const [tplLoading, setTplLoading] = useState(false);
  const [preset, setPreset] = useState<QueryPreset | null>(null);
  const [isCreateMode, setIsCreateMode] = useState(false);
  const [hasDirtyChanges, setHasDirtyChanges] = useState(false);

  const saveRef = useRef<(() => void | Promise<void>) | null>(null);

  useEffect(() => {
    const run = async () => {
      setTplLoading(true);
      try {
        const list = await getQueryTemplates({ pageNum: 1, pageSize: 100 });
        const data = list.data ?? [];
        setTplOpts(mapQueryTemplatesToOptions(data));
        const def = data.find((t) => t.isDefault)?.queryNo ?? data[0]?.queryNo ?? '';
        if (!isCreateMode && !templateId && def) {
          setTemplateId(def);
        }
      } finally {
        setTplLoading(false);
      }
    };
    void run();
  }, [templateId, isCreateMode]);

  const applyDetailToPreset = (d: QueryTemplateDetailResult, id: string) => {
    const transformation = d.transformation?.no ?? '';
    const searchAlgorithm = d.retrieval?.no ?? '';

    let semanticTopK = 30;
    let semanticThreshold = 0.4;
    let keywordTopK = 30;
    let rerankerTopK = 10;
    let rerankerType = 'weighted';
    let rerankerWeight = 0.4;

    const rp = d.retrieval?.parameters;

    if (isSemanticParams(rp)) {
      // { type: 'semantic', semantic: { topK, threshold } }
      semanticTopK = num(rp.semantic?.topK, semanticTopK);
      semanticThreshold = num(rp.semantic?.threshold, semanticThreshold);
    } else if (isHybridParams(rp)) {
      // { type: 'hybrid', semantic, keyword, reranker }
      semanticTopK = num(rp.semantic?.topK, semanticTopK);
      semanticThreshold = num(rp.semantic?.threshold, semanticThreshold);
      keywordTopK = num(rp.keyword?.topK, keywordTopK);
      rerankerTopK = num(rp.reranker?.topK, rerankerTopK);
      rerankerType = rp.reranker?.type ?? rerankerType;
      rerankerWeight = num(rp.reranker?.weight, rerankerWeight);
    }

    const reranking = d.reranking?.no ?? '';
    const llmModel = d.generation?.no ?? '';

    let temperature = 0.2;
    let multimodal = false;

    if (isGenerationParams(d.generation?.parameters)) {
      temperature = num(d.generation.parameters?.temperature, temperature);
      multimodal = bool(d.generation.parameters?.multimodal, multimodal);
    }

    const nextPreset: QueryPreset = {
      template: id,
      transformation,
      searchAlgorithm,
      reranking,
      llmModel,
      temperature,
      multimodal,
      isDefault: !!d.isDefault,
      semanticTopK,
      semanticThreshold,
      keywordTopK,
      rerankerTopK,
      rerankerType,
      rerankerWeight,
    };

    setPreset(nextPreset);
  };

  useEffect(() => {
    const run = async () => {
      if (!templateId || isCreateMode) {
        setPreset(null);
        return;
      }
      const detail = await getQueryTemplateDetail(templateId);
      applyDetailToPreset(detail, templateId);
    };
    void run();
  }, [templateId, isCreateMode]);

  const mergedOptions: RagOptions | null = useMemo(
    () => (ragOptions ? { ...ragOptions, queryTemplate: tplOpts } : null),
    [ragOptions, tplOpts]
  );

  const handleCreateNew = () => {
    setIsCreateMode(true);
    setTemplateId('');
    setPreset(null);
  };

  const handleQuerySave = async (payload: {
    template: string;
    templateName: string;
    transformation: string;
    searchAlgorithm: string;
    reranking: string;
    llmModel: string;
    temperature: number;
    multimodal: boolean;
    isDefault: boolean;
    isCreateMode?: boolean;
    semanticTopK: number;
    semanticThreshold: number;
    keywordTopK: number;
    rerankerTopK: number;
    rerankerType: string;
    rerankerWeight: number;
  }) => {
    const isHybrid = !!ragOptions?.searchHybrid?.some((o) => o.value === payload.searchAlgorithm);

    const dto = {
      name: payload.templateName,
      transformation: { no: payload.transformation },
      retrieval: {
        no: payload.searchAlgorithm,
        parameters: isHybrid
          ? {
              type: 'hybrid',
              semantic: {
                topK: payload.semanticTopK,
                threshold: payload.semanticThreshold,
              },
              keyword: {
                topK: payload.keywordTopK,
              },
              reranker: {
                topK: payload.rerankerTopK,
                type: payload.rerankerType,
                weight: payload.rerankerWeight,
              },
            }
          : {
              type: 'semantic',
              semantic: {
                topK: payload.semanticTopK,
                threshold: payload.semanticThreshold,
              },
            },
      },
      reranking: payload.reranking ? { no: payload.reranking } : undefined,
      generation: {
        no: payload.llmModel,
        parameters: {
          temperature: payload.temperature,
          multimodal: payload.multimodal,
        },
      },
      isDefault: payload.isDefault,
    };

    if (isCreateMode) {
      const created = await createQueryTemplate(dto);
      const [detail, list] = await Promise.all([
        getQueryTemplateDetail(created.queryNo),
        getQueryTemplates({ pageNum: 1, pageSize: 100 }),
      ]);

      setTplOpts(mapQueryTemplatesToOptions(list.data ?? []));
      setTemplateId(created.queryNo);
      setIsCreateMode(false);
      applyDetailToPreset(detail, created.queryNo);
      onCreate?.();
      return;
    }

    await putQueryTemplate(payload.template, dto);

    const [detail, list] = await Promise.all([
      getQueryTemplateDetail(payload.template),
      getQueryTemplates({ pageNum: 1, pageSize: 100 }),
    ]);

    applyDetailToPreset(detail, payload.template);
    setTplOpts(mapQueryTemplatesToOptions(list.data ?? []));
  };

  return (
    <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      <div>
        <div ref={anchors['query-embed']} />
        <div ref={anchors.searching} />
        <div ref={anchors.reranker} />
        <div ref={anchors.prompting} />
        <div ref={anchors.generation} />

        <QuerySettingsForm
          template={templateId}
          isCreateMode={isCreateMode}
          options={mergedOptions ?? undefined}
          loading={optionsLoading || tplLoading}
          preset={preset ?? undefined}
          onSave={handleQuerySave}
          onDirtyChange={(dirty) => setHasDirtyChanges(dirty)}
          registerSaveHandler={(fn) => {
            saveRef.current = fn;
          }}
        />
      </div>

      <aside className="space-y-4 sticky top-20 h-fit">
        <TemplateList
          kind="query"
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
