export type Collection = {
  id: string;
  name: string;
  ingestTemplate?: string;
};

export type QueryTemplate = {
  id: string;
  name: string;
  description?: string;
  body: string;
};

export type IngestStrategy = {
  id: string;
  name: string;
  notes?: string;
};

export type QueryStrategy = {
  id: string;
  name: string;
  body: string;
};

// 스트리밍 이벤트 타입 정의
export type IngestStreamEvent = {
  event: string;
  data: IngestStreamProgress | IngestStreamSummary | string;
};

export type IngestStreamProgress = {
  eventType: 'STEP_UPDATE' | 'RUN_COMPLETED' | 'RUN_FAILED';
  userId: string;
  fileNo: string;
  currentStep: 'UPLOAD' | 'EXTRACTION' | 'EMBEDDING' | 'VECTOR_STORE';
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  processed: number;
  total: number | null;
  progressPct: number;
  overallPct: number;
  ts: number | null;
};

export type IngestStreamSummary = {
  completed: number;
  total: number;
};
