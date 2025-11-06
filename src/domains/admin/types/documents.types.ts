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
export type CollectionList = {
  collections: Array<collectionType>;
};
export type collectionType = {
  collection: string;
  createdAt: string;
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
  pagination: pagination;
};
export type documentDatatype = {
  fileNo: number;
  name: string;
  size: string;
  type: string;
  uploadedAt: string;
  category: string;
  offerNo: string;
  collection: string;
};

// 컬렉션 환경 타입
export type CollectionEnv = 'all' | 'prod' | 'test' | 'prod';
