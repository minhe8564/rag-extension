import type { Option } from '@/shared/components/controls/Select';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

export type SavePayload = {
  template: string;
  templateName: string;
  extractEngine: string;
  chunkStrategy: string;
  chunkSize: number;
  overlap: number;
  embedModel: string;
  embedSparse: string;
  isCreateMode?: boolean;
  isDefault: boolean;
};

export type IngestPreset = {
  template: string;
  extractEngine?: string;
  chunkStrategy?: string;
  chunkSize?: number;
  overlap?: number;
  embedModel?: string;
  embedSparse?: string;
  isDefault?: boolean;
};

export type Anchors = Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;

export type IngestSettingsFormProps = {
  template: string;
  isCreateMode?: boolean;
  onSave?: (payload: SavePayload) => void | Promise<void>;
  options?: RagOptions | null;
  loading?: boolean;
  anchors?: Anchors;
  preset?: IngestPreset;
  onDirtyChange?: (dirty: boolean) => void;
  registerSaveHandler?: (handler: () => void | Promise<void>) => void;
};

export type CommonSelects = {
  templateOpts: Option[];
  extractOpts: Option[];
  chunkOpts: Option[];
  embedDenseOpts: Option[];
  embedSparseOpts: Option[];
};

export type IngestSettingsFieldsProps = {
  anchors?: Anchors;
  loading?: boolean;
  scrollTo: (id: FlowStepId) => void;

  // values
  extractEngine: string;
  chunkStrategy: string;
  chunkSize: number;
  overlap: number;
  embedModel: string;
  embedSparse: string;

  // handlers
  setExtractEngine: (v: string) => void;
  setChunkStrategy: (v: string) => void;
  setChunkSize: (v: number) => void;
  setOverlap: (v: number) => void;
  setEmbedModel: (v: string) => void;
  setEmbedSparse: (v: string) => void;

  // options
  extractOpts: Option[];
  chunkOpts: Option[];
  embedDenseOpts: Option[];
  embedSparseOpts: Option[];
};
