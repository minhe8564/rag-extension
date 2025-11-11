// src/domains/admin/types/rag-settings/template.types.ts
import type { Pagination } from '@/shared/lib/api.types';

// 리스트 공통 아이템
export interface IngestTemplateListItem {
  ingestNo: string;
  name: string;
  isDefault: boolean;
}

export interface QueryTemplateListItem {
  queryNo: string;
  name: string;
  isDefault: boolean;
}

// 리스트 결과
export interface IngestTemplateListResult {
  data: IngestTemplateListItem[];
  pagination: Pagination;
}

export interface QueryTemplateListResult {
  data: QueryTemplateListItem[];
  pagination: Pagination;
}

// 전략 참조(상세/업서트 공통)
export interface StrategyRef {
  no: string;
  code?: string;
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
}

// 상세 결과(Ingest)
export interface IngestTemplateDetailResult {
  ingestNo: string;
  name: string;
  isDefault: boolean;
  extractions: StrategyRef[]; // 다중
  chunking: StrategyRef; // 단일
  denseEmbeddings: StrategyRef[]; // 다중
  sparseEmbedding?: StrategyRef; // 단일 (optional)  ← sparse로 통일
}

// 상세 결과(Query)
export interface QueryTemplateDetailResult {
  queryNo: string;
  name: string;
  isDefault: boolean;
  transformations: StrategyRef[]; // 다중 (HyDE/Buffer 등)
  retrieval: StrategyRef; // 단일 (semantic/hybrid)
  reranking?: StrategyRef; // 단일 (optional)
  promptingSystem?: StrategyRef[]; // 다중 (optional)
  promptingUser?: StrategyRef[]; // 다중 (optional)
  generation: StrategyRef; // 단일
}

// 업서트용 입력 DTO
export interface StrategyRefInput {
  no: string;
  parameters?: Record<string, unknown>;
}

// Ingest 업서트
export interface UpsertIngestTemplateDto {
  name: string;
  isDefault?: boolean;
  extractions: StrategyRefInput[];
  chunking: StrategyRefInput;
  denseEmbeddings: StrategyRefInput[];
  sparseEmbedding?: StrategyRefInput;
}

// Query 업서트
export interface UpsertQueryTemplateDto {
  name: string;
  isDefault?: boolean;
  transformations: StrategyRefInput[];
  retrieval: StrategyRefInput;
  reranking?: StrategyRefInput;
  promptingSystem?: StrategyRefInput[];
  promptingUser?: StrategyRefInput[];
  generation: StrategyRefInput;
}
