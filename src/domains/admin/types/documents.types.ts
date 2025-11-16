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
  status: string;
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

export type VectorizationStep = {
  type: 'UPLOAD' | 'EXTRACTION' | 'EMBEDDING' | 'VECTOR_STORE';
  percentage: number;
};

export type VectorizationItem = {
  userId: string;
  fileNo: string;
  fileName: string;
  fileCategory: string;
  bucket: string;
  size: number;

  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  currentStep: 'UPLOAD' | 'EXTRACTION' | 'EMBEDDING' | 'VECTOR_STORE';

  progressPct: number;
  overallPct: number;
  createdAt: number;
  updatedAt: number;

  steps: VectorizationStep[];
};
