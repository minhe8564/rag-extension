export type data = {
  fileNo: string;
  name: string;
  size: number | null;
  type: string;
  uploadedAt: string;
  category: string;
  offerNo: string;
  collection: string;
};

export interface ColSectionProps {
  selectedCollection: 'public' | 'hebees' | null;
  onCollectionSelect: (collectionName: 'public' | 'hebees' | null) => void;
}

export interface UploadedDocumentsProps {
  files: data[];
  onFilesChange?: (updatedFiles: data[]) => void; // 부모에 반영하고 싶을 때 사용
  onSelectFiles: (selectedFiles: data[]) => void; // 컬렉션 선택으로 넘길 파일을 부모로 전달
  selectedFiles: data[];
}
export type pagination = {
  pageNum: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
};

// 컬렉션 목록 조회 타입
export type dataType = {
  data: Array<collectionType>;
  pagination: paginationType;
  hasNext: boolean;
  nextCursor: cursorType;
};
export type collectionType = {
  collectionNo: string;
  name: string;
  version: number;
  ingestGroupNo: string;
  createdAt: string;
};
export type paginationType = {
  pageNum: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
};
export type cursorType = {
  cursorCreatedAt: string;
  cursorId: string;
};
// export type getCollections = {
//   data: Array<datatype>;
//   pagination: pagination;
// };
// export type datatype = {
//   collectionNo: number;
//   name: string;
//   env: CollectionEnv;
//   offerNo: string;
// };

// 컬렉션 내 문서 목록 조회
export type getDocumentsInCollection = {
  data: Array<documentDatatype>;
  pagination: paginationType;
  hasNext: boolean;
  nextCursor: cursorType;
};
export type documentDatatype = {
  fileNo: string;
  name: string;
  size: string;
  type: string;
  bucket: string;
  path: string;
  categoryNo: string;
  collectionNo: string;
  createdAt: string;
};

// 컬렉션 환경 타입
export type CollectionEnv = 'all' | 'prod' | 'test' | 'prod';

export type FileType = {
  name: string;
  size: number | null;
  category: string | null;
  collection: 'public' | 'hebees' | null;
  currentProgress: string | null;
  currentPercent: number | null;
  totalProgress: number | null;
};

// 진행률 최초 조회 요청
export type GetVectorizationProgressParams = {
  page?: number; // 기본값 1
  status?: string; //"RUNNING,QUEUED"
  pipeline?: string; // "pdf-default"
  docId?: number; // 특정 문서만 조회
};

// 진행률 최초 조회 응답
export type GetVectorizationProgress = {
  items: VectorizationItem[];
  page: number;
  size: number;
  hasNext: boolean;
  hasPrev: boolean;
};
// (steps안)각 단계별 상세 진행 상태
export type VectorizationStep = {
  step: 'CLEAN' | 'EMBED' | 'UPSERT';
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  unit: 'PAGE' | 'CHUNK' | 'RECORD';
  processed: number;
  total: number;
  progressPct: number;
  startedAt: string | null;
  finishedAt: string | null;
};
// (큐) 상태 정보
export type VectorizationQueue = {
  position: number;
  concurrencyLimit: number;
};
// (items안)각 문서별 벡터화 실행 단위
export type VectorizationItem = {
  runId: number;
  docId: number;
  docName: string;
  pipeline: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  currentStep: 'CLEAN' | 'EMBED' | 'UPSERT' | null;
  overallPct: number; // 전체 진행률
  version: number;
  createdAt: string;
  enqueuedAt: string | null;
  startedAt: string | null;
  updatedAt: string | null;
  queue: VectorizationQueue;
  etaSec: number | null; // 예상 남은 시간(초)
  lastError: string | null;
  steps: VectorizationStep[];
};
