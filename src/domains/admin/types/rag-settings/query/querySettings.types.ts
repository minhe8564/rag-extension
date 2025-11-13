import type { Option } from '@/shared/components/Select';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

export type SavePayload = {
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
};

export type QueryPreset = {
  template: string;
  transformation?: string;
  searchAlgorithm?: string;
  reranking?: string;
  llmModel?: string;
  temperature?: number;
  multimodal?: boolean;
  isDefault: boolean;

  semanticTopK?: number;
  semanticThreshold?: number;
  keywordTopK?: number;
  rerankerTopK?: number;
  rerankerType?: string;
  rerankerWeight?: number;
};

export type Anchors = Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;

export type QuerySettingsFormProps = {
  template: string;
  isCreateMode?: boolean;
  onSave?: (payload: SavePayload) => void | Promise<void>;
  options?: RagOptions | null;
  loading?: boolean;
  anchors?: Anchors;
  preset?: QueryPreset;
};

export type CommonSelects = {
  templateOpts: Option[];
  transformOpts: Option[];
  searchAlgoOpts: Option[];
  rerankOpts: Option[];
  llmOpts: Option[];
};

export type QuerySettingsFieldsProps = {
  anchors?: Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;
  loading: boolean;
  scrollTo: (id: FlowStepId) => void;

  transformation: string;
  searchAlgorithm: string;
  reranking: string;
  llmModel: string;
  temperature: number;
  multimodal: boolean;

  setTransformation: (v: string) => void;
  setSearchAlgorithm: (v: string) => void;
  setReranking: (v: string) => void;
  setLlmModel: (v: string) => void;
  setTemperature: (v: number) => void;
  setMultimodal: (v: boolean) => void;

  transformOpts: Option[];
  searchAlgoOpts: Option[];
  rerankOpts: Option[];
  llmOpts: Option[];

  searchAlgoType?: 'semantic' | 'hybrid' | null;

  semanticTopK: number;
  semanticThreshold: number;
  keywordTopK: number;
  rerankerTopK: number;
  rerankerWeight: number;
  rerankerType: string;

  setSemanticTopK: (v: number) => void;
  setSemanticThreshold: (v: number) => void;
  setKeywordTopK: (v: number) => void;
  setRerankerTopK: (v: number) => void;
  setRerankerWeight: (v: number) => void;
  setRerankerType: (v: string) => void;
};
