import { useEffect, useMemo, useState } from 'react';
import type { Option } from '@/shared/components/Select';
import { QuerySettingsForm } from '@/domains/admin/components/rag-settings/query/QuerySettingsForm';
import TemplateList from '@/domains/admin/components/rag-settings/TemplateList';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

import {
  getQueryTemplates,
  getQueryTemplateDetail,
  patchQueryTemplate,
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

export type QueryPreset = {
  template: string;
  queryEngine: string;
  searchAlgorithm: string;
  topK: number;
  threshold: number;
  reranking: string;
  llmModel: string;
  temperature: number;
  multimodal: boolean;
};

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

  useEffect(() => {
    const run = async () => {
      setTplLoading(true);
      try {
        const list = await getQueryTemplates({ pageNum: 1, pageSize: 100 });
        setTplOpts(mapQueryTemplatesToOptions(list.data ?? []));
        const def =
          (list.data ?? []).find((t) => t.isDefault)?.queryNo ??
          (list.data ?? [])[0]?.queryNo ??
          '';
        if (!templateId && def) setTemplateId(def);
      } finally {
        setTplLoading(false);
      }
    };
    void run();
  }, [templateId]);

  useEffect(() => {
    const apply = (d: QueryTemplateDetailResult, id: string) => {
      const queryEngine = d.transformations?.[0]?.no ?? '';
      const searchAlgorithm = d.retrieval?.no ?? '';

      let topK = 5;
      let threshold = 0.2;
      const rp = d.retrieval?.parameters;
      if (isSemanticParams(rp)) {
        topK = num(rp.semantic?.topK, topK);
        threshold = num(rp.semantic?.threshold, threshold);
      } else if (isHybridParams(rp)) {
        topK = num(rp.semantic?.topK, num(rp.keyword?.topK, num(rp.reranker?.topK, topK)));
        threshold = num(rp.semantic?.threshold, threshold);
      }

      const reranking = d.reranking?.no ?? '';
      const llmModel = d.generation?.no ?? '';

      let temperature = 0.2;
      let multimodal = false;
      if (isGenerationParams(d.generation?.parameters)) {
        temperature = num(d.generation.parameters?.temperature, temperature);
        multimodal = bool(d.generation.parameters?.multimodal, multimodal);
      }

      setPreset({
        template: id,
        queryEngine,
        searchAlgorithm,
        topK,
        threshold,
        reranking,
        llmModel,
        temperature,
        multimodal,
      });
    };

    const run = async () => {
      if (!templateId || isCreateMode) {
        setPreset(null);
        return;
      }
      const d = await getQueryTemplateDetail(templateId);
      apply(d, templateId);
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
    queryEngine: string;
    searchAlgorithm: string;
    topK: number;
    threshold: number;
    reranking: string;
    llmModel: string;
    temperature: number;
    multimodal: boolean;
  }) => {
    const isHybrid = !!ragOptions?.searchHybrid?.some((o) => o.value === payload.searchAlgorithm);

    const dto = {
      name: payload.templateName,
      transformations: payload.queryEngine ? [{ no: payload.queryEngine }] : [],
      retrieval: {
        no: payload.searchAlgorithm,
        parameters: isHybrid
          ? {
              semantic: { topK: payload.topK, threshold: payload.threshold },
              keyword: { topK: payload.topK },
              reranker: { topK: payload.topK },
            }
          : { semantic: { topK: payload.topK, threshold: payload.threshold } },
      },
      reranking: payload.reranking ? { no: payload.reranking } : undefined,
      generation: {
        no: payload.llmModel,
        parameters: { temperature: payload.temperature, multimodal: payload.multimodal },
      },
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

      const applyCreated = (d: QueryTemplateDetailResult) => {
        const queryEngine = d.transformations?.[0]?.no ?? '';
        const searchAlgorithm = d.retrieval?.no ?? '';
        let topK = 5;
        let threshold = 0.2;
        const rp = d.retrieval?.parameters;
        if (isSemanticParams(rp)) {
          topK = num(rp.semantic?.topK, topK);
          threshold = num(rp.semantic?.threshold, threshold);
        } else if (isHybridParams(rp)) {
          topK = num(rp.semantic?.topK, num(rp.keyword?.topK, num(rp.reranker?.topK, topK)));
          threshold = num(rp.semantic?.threshold, threshold);
        }
        const reranking = d.reranking?.no ?? '';
        const llmModel = d.generation?.no ?? '';
        let temperature = 0.2;
        let multimodal = false;
        if (isGenerationParams(d.generation?.parameters)) {
          temperature = num(d.generation.parameters?.temperature, temperature);
          multimodal = bool(d.generation.parameters?.multimodal, multimodal);
        }
        setPreset({
          template: created.queryNo,
          queryEngine,
          searchAlgorithm,
          topK,
          threshold,
          reranking,
          llmModel,
          temperature,
          multimodal,
        });
      };
      applyCreated(detail);
      onCreate?.();
      return;
    }

    await patchQueryTemplate(payload.template, dto);

    const [detail, list] = await Promise.all([
      getQueryTemplateDetail(payload.template),
      getQueryTemplates({ pageNum: 1, pageSize: 100 }),
    ]);

    {
      const queryEngine = detail.transformations?.[0]?.no ?? '';
      const searchAlgorithm = detail.retrieval?.no ?? '';
      let topK = 5;
      let threshold = 0.2;
      const rp = detail.retrieval?.parameters;
      if (isSemanticParams(rp)) {
        topK = num(rp.semantic?.topK, topK);
        threshold = num(rp.semantic?.threshold, threshold);
      } else if (isHybridParams(rp)) {
        topK = num(rp.semantic?.topK, num(rp.keyword?.topK, num(rp.reranker?.topK, topK)));
        threshold = num(rp.semantic?.threshold, threshold);
      }
      const reranking = detail.reranking?.no ?? '';
      const llmModel = detail.generation?.no ?? '';
      let temperature = 0.2;
      let multimodal = false;
      if (isGenerationParams(detail.generation?.parameters)) {
        temperature = num(detail.generation.parameters?.temperature, temperature);
        multimodal = bool(detail.generation.parameters?.multimodal, multimodal);
      }
      setPreset({
        template: payload.template,
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
        />
      </div>

      <aside className="space-y-4">
        <TemplateList
          kind="query"
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
