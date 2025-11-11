export const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null;

export const num = (v: unknown, fallback: number): number =>
  typeof v === 'number' && Number.isFinite(v) ? v : fallback;

export const bool = (v: unknown, fallback: boolean): boolean =>
  typeof v === 'boolean' ? v : fallback;

// Ingest: chunking.parameters { token, overlap }
export const isChunkingParams = (p: unknown): p is { token?: number; overlap?: number } =>
  isRecord(p) &&
  (typeof p.token === 'number' || typeof p.token === 'undefined') &&
  (typeof p.overlap === 'number' || typeof p.overlap === 'undefined');

// Query: retrieval.parameters (semantic | hybrid)
export type SemanticParams = { type: 'semantic'; semantic?: { topK?: number; threshold?: number } };
export type HybridParams = {
  type: 'hybrid';
  keyword?: { topK?: number };
  semantic?: { topK?: number; threshold?: number };
  reranker?: { topK?: number };
};

export const isSemanticParams = (p: unknown): p is SemanticParams =>
  isRecord(p) &&
  p.type === 'semantic' &&
  (p.semantic === undefined ||
    (isRecord(p.semantic) &&
      (typeof p.semantic.topK === 'number' || typeof p.semantic.topK === 'undefined') &&
      (typeof p.semantic.threshold === 'number' || typeof p.semantic.threshold === 'undefined')));

export const isHybridParams = (p: unknown): p is HybridParams =>
  isRecord(p) &&
  p.type === 'hybrid' &&
  (p.keyword === undefined ||
    (isRecord(p.keyword) &&
      (typeof p.keyword.topK === 'number' || typeof p.keyword.topK === 'undefined'))) &&
  (p.semantic === undefined ||
    (isRecord(p.semantic) &&
      (typeof p.semantic.topK === 'number' || typeof p.semantic.topK === 'undefined') &&
      (typeof p.semantic.threshold === 'number' || typeof p.semantic.threshold === 'undefined'))) &&
  (p.reranker === undefined ||
    (isRecord(p.reranker) &&
      (typeof p.reranker.topK === 'number' || typeof p.reranker.topK === 'undefined')));

// Query: generation.parameters { temperature, multimodal }
export const isGenerationParams = (
  p: unknown
): p is { temperature?: number; multimodal?: boolean } =>
  isRecord(p) &&
  (typeof p.temperature === 'number' || typeof p.temperature === 'undefined') &&
  (typeof p.multimodal === 'boolean' || typeof p.multimodal === 'undefined');
