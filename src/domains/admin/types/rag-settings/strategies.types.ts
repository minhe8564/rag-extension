// 요청 시 사용할 전략 타입 (쿼리용)
export type StrategyTypeQuery =
  | 'extraction'
  | 'chunking'
  | 'embedding-dense'
  | 'embedding-spare'
  | 'embedding-sparse'
  | 'transformation'
  | 'retrieval'
  | 'reranking'
  | 'prompting-user'
  | 'prompting-system'
  | 'generation';

// 응답 전략 타입
export type StrategyType =
  | 'extraction'
  | 'chunking'
  | 'embedding-dense'
  | 'embedding-sparse'
  | 'transformation'
  | 'retrieval'
  | 'reranking'
  | 'prompting-user'
  | 'prompting-system'
  | 'generation';

// Extraction
export interface ExtractionParameter {
  type: string; // "marker" | "pyMuPDF"
  fileType: string; // "pdf"
}

// Chunking
export interface ChunkingParameter {
  type: 'md' | 'fixed' | 'semantic';
  token: number;
  overlap: number;
}

// Dense Embedding
export interface EmbeddingDenseParameter {
  type: 'dense';
  model: string;
}

// Sparse Embedding
export interface EmbeddingSparseParameter {
  type: 'spare' | 'sparse';
  model: string;
}

// Transformation
export interface TransformationParameter {
  type: 'buffer' | 'HyDE' | string;
}

// Retrieval (semantic)
export interface RetrievalSemanticParameter {
  type: 'semantic';
  semantic?: { topK: number; threshold: number };
}

// Retrieval (hybrid)
export interface RetrievalHybridParameter {
  type: 'hybrid';
  keyword: { topK: number };
  semantic?: { topK: number; threshold: number };
  reranker: {
    type: string;
    weight: number;
    topK?: number;
  };
}

// Reranking
export interface RerankingParameter {
  topK: number;
  model: string;
}

// Prompting (user)
export interface PromptUserParameter {
  type: 'user';
  content: string;
}

// Prompting (system)
export interface PromptSystemParameter {
  type: 'system';
  content: string;
}

// Generation
export interface GenerationParameter {
  model: string;
  provider: string;
  timeout: number;
  max_tokens: number;
  max_retries: number;
  temperature: number;
}

// fallback parameter 타입
// any 대신 unknown + Partial 형태
export type UnknownParameter = Partial<Record<string, unknown>>;

// 통합 parameter 타입
export type StrategyParameter =
  | ExtractionParameter
  | ChunkingParameter
  | EmbeddingDenseParameter
  | EmbeddingSparseParameter
  | TransformationParameter
  | RetrievalSemanticParameter
  | RetrievalHybridParameter
  | RerankingParameter
  | PromptUserParameter
  | PromptSystemParameter
  | GenerationParameter
  | UnknownParameter;

// Strategy 엔티티
export interface Strategy {
  strategyNo: string;
  code?: string;
  name: string;
  description: string;
  type: StrategyType;
  parameter?: StrategyParameter;
}

// 목록 결과
export interface StrategyListResult {
  data: Strategy[];
}

// 목록 조회 요청 쿼리
export interface GetStrategiesParams {
  type?: StrategyTypeQuery;
  pageNum?: number;
  pageSize?: number;
}
