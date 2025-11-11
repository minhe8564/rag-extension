import type { Option } from '@/shared/components/Select';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

export type SavePayload = {
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

export type QueryPreset = {
  queryEngine?: string;
  searchAlgorithm?: string;
  topK?: number;
  threshold?: number;
  reranking?: string;
  llmModel?: string;
  temperature?: number;
  multimodal?: boolean;
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
  anchors?: Anchors;
  loading?: boolean;
  scrollTo: (id: FlowStepId) => void;

  // values
  queryEngine: string;
  searchAlgorithm: string;
  topK: number;
  threshold: number;
  reranking: string;
  llmModel: string;
  temperature: number;
  multimodal: boolean;

  // handlers
  setQueryEngine: (v: string) => void;
  setSearchAlgorithm: (v: string) => void;
  setTopK: (v: number) => void;
  setThreshold: (v: number) => void;
  setReranking: (v: string) => void;
  setLlmModel: (v: string) => void;
  setTemperature: (v: number) => void;
  setMultimodal: (v: boolean) => void;

  // options
  transformOpts: Option[];
  searchAlgoOpts: Option[];
  rerankOpts: Option[];
  llmOpts: Option[];
};
